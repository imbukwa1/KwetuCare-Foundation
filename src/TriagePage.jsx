import { useCallback, useEffect, useMemo, useState } from "react";
import logo from "./kcf logo.jpeg";
import "./TriagePage.css";
import { fetchQueue, submitTriage } from "./api";
import useHybridDataSync from "./useHybridDataSync";

const DOCTOR_TYPE_OPTIONS = [
  { value: "general_doctor", label: "General Doctor" },
  { value: "pediatrician", label: "Pediatrician" },
  { value: "gynecologist", label: "Gynecologist" },
  { value: "obstetrician", label: "Obstetrician" },
  { value: "nutritionist", label: "Nutritionist" },
  { value: "dental", label: "Dentist" },
  { value: "optician", label: "Optician" },
];

function Header({ nurseName, onLogout }) {
  return (
    <header className="triage-header">
      <div className="triage-logo">
        <img src={logo} alt="KCF logo" className="site-logo" />
      </div>
      <h1>Triage</h1>
      <div className="triage-profile">
        <span>{nurseName}</span>
        <button className="triage-logout" onClick={onLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}

function PatientCard({ patient, onStart }) {
  return (
    <article className={`patient-card ${patient.priority === "urgent" ? "patient-card-urgent" : ""}`}>
      <div>
        <h3>{patient.name}</h3>
        <p>ID: {patient.id}</p>
        <p>Reg No: {patient.reg_no}</p>
        <p>Camp: {patient.camp}</p>
        <p>Priority: {patient.priority}</p>
      </div>
      <button className="btn-primary" onClick={() => onStart(patient)}>
        Start Triage
      </button>
    </article>
  );
}

function PatientList({ patients, onStart }) {
  return (
    <section className="patient-list">
      <h2>Patients List</h2>
      {patients.length === 0 ? (
        <p className="queue-empty">No patients are currently waiting for triage.</p>
      ) : (
        <div className="cards-grid">
          {patients.map((patient) => (
            <PatientCard key={patient.id} patient={patient} onStart={onStart} />
          ))}
        </div>
      )}
    </section>
  );
}

function TriageModal({ isOpen, patient, onClose, onSubmit }) {
  const [form, setForm] = useState({
    bloodPressure: "",
    requiresBloodSugarCheck: false,
    assignedDoctorType: "general_doctor",
    heartRate: "",
    respiratoryRate: "",
    spo2: "",
    temperature: "",
    weight: "",
    height: "",
    notes: "",
  });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const computedBmi = useMemo(() => {
    const weight = Number(form.weight);
    const height = Number(form.height);

    if (!weight || !height || height <= 0) {
      return "";
    }

    return (weight / (height * height)).toFixed(2);
  }, [form.height, form.weight]);

  const isFormValid = useMemo(() => {
    return (
      form.bloodPressure.trim() !== "" &&
      (form.requiresBloodSugarCheck || form.assignedDoctorType.trim() !== "") &&
      form.heartRate.trim() !== "" &&
      form.respiratoryRate.trim() !== "" &&
      form.spo2.trim() !== "" &&
      form.temperature.trim() !== "" &&
      form.weight.trim() !== "" &&
      form.height.trim() !== ""
    );
  }, [form]);

  const handleField = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleToggleBloodSugar = (event) => {
    const checked = event.target.checked;
    setForm((prev) => ({
      ...prev,
      requiresBloodSugarCheck: checked,
      assignedDoctorType: checked ? "" : prev.assignedDoctorType || "general_doctor",
    }));
  };

  const submit = (event) => {
    event.preventDefault();
    if (!isFormValid) {
      setError("Please fill all required fields.");
      return;
    }

    setError("");
    setIsSubmitting(true);

    Promise.resolve(
      onSubmit({
        patient,
        bloodPressure: form.bloodPressure.trim(),
        requiresBloodSugarCheck: form.requiresBloodSugarCheck,
        assignedDoctorType: form.assignedDoctorType,
        heartRate: Number(form.heartRate),
        respiratoryRate: Number(form.respiratoryRate),
        spo2: Number(form.spo2),
        temperature: Number(form.temperature),
        weight: Number(form.weight),
        height: Number(form.height),
        notes: form.notes,
      })
    )
      .then(() => {
        setForm({
          bloodPressure: "",
          requiresBloodSugarCheck: false,
          assignedDoctorType: "general_doctor",
          heartRate: "",
          respiratoryRate: "",
          spo2: "",
          temperature: "",
          weight: "",
          height: "",
          notes: "",
        });
      })
      .catch((submitError) => {
        setError(submitError.message);
      })
      .finally(() => setIsSubmitting(false));
  };

  if (!isOpen || !patient) return null;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Triage for {patient.name}</h3>
          <button className="close-btn" onClick={onClose}>
            x
          </button>
        </div>
        <form onSubmit={submit} className="modal-form">
          <label>
            Blood Pressure *
            <input
              type="text"
              value={form.bloodPressure}
              onChange={handleField("bloodPressure")}
              placeholder="e.g. 120/80"
            />
          </label>
          <label className="triage-checkbox-row">
            <input
              type="checkbox"
              checked={form.requiresBloodSugarCheck}
              onChange={handleToggleBloodSugar}
            />
            <span>Requires Blood Sugar Check</span>
          </label>
          {!form.requiresBloodSugarCheck && (
            <label>
              Refer to Doctor Type *
              <select value={form.assignedDoctorType} onChange={handleField("assignedDoctorType")}>
                {DOCTOR_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          )}
          <label>
            Heart Rate (bpm) *
            <input type="number" value={form.heartRate} onChange={handleField("heartRate")} placeholder="e.g. 82" />
          </label>
          <label>
            Respiratory Rate (RR) *
            <input
              type="number"
              value={form.respiratoryRate}
              onChange={handleField("respiratoryRate")}
              placeholder="e.g. 18"
            />
          </label>
          <label>
            Oxygen Saturation (SpO2) *
            <input type="number" value={form.spo2} onChange={handleField("spo2")} placeholder="e.g. 98" />
          </label>
          <label>
            Temperature (C) *
            <input type="number" value={form.temperature} step="0.1" onChange={handleField("temperature")} placeholder="e.g. 36.8" />
          </label>
          <label>
            Weight (kg) *
            <input type="number" value={form.weight} step="0.1" onChange={handleField("weight")} placeholder="e.g. 64" />
          </label>
          <label>
            Height (m) *
            <input type="number" value={form.height} step="0.01" onChange={handleField("height")} placeholder="e.g. 1.25" />
          </label>
          <label>
            BMI
            <input type="text" value={computedBmi} readOnly placeholder="Calculated automatically" />
          </label>
          <label>
            Nurse Notes
            <textarea value={form.notes} onChange={handleField("notes")} rows={3} placeholder="Observations, symptoms..." />
          </label>
          {error && <p className="modal-error">{error}</p>}
          <div className="modal-actions">
            <button type="button" className="btn-muted" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={!isFormValid || isSubmitting}>
              {isSubmitting ? "Submitting..." : "Submit"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function TriagePage({ currentUser, onLogout }) {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const loadQueue = useCallback(async ({ showLoading = false } = {}) => {
    if (showLoading) {
      setLoading(true);
    }
    const queue = await fetchQueue();
    return queue;
  }, []);

  const { lastUpdated, refresh } = useHybridDataSync({
    fetcher: loadQueue,
    onData: (queue, { showLoading }) => {
      setPatients(queue);
      if (showLoading) {
        setLoading(false);
      }
    },
    onError: (error, { showLoading }) => {
      setPageError(error.message);
      if (showLoading) {
        setLoading(false);
      }
    },
    relevantEventTypes: ["patient_created", "triage_completed"],
  });

  useEffect(() => {
    refresh({ showLoading: true, source: "initial" }).catch(() => {});
  }, [refresh]);

  const openTriage = useCallback((patient) => {
    setSelectedPatient(patient);
    setModalOpen(true);
    setPageError("");
  }, []);

  const closeTriage = useCallback(() => {
    setModalOpen(false);
    setSelectedPatient(null);
  }, []);

  const handleSubmit = useCallback(async (triageData) => {
    setPageError("");
    const triagePayload = {
      patient_id: triageData.patient.id,
      blood_pressure: triageData.bloodPressure,
      requires_blood_sugar_check: triageData.requiresBloodSugarCheck,
      temperature: triageData.temperature,
      weight: triageData.weight,
      height: triageData.height,
      heart_rate: triageData.heartRate,
      respiratory_rate: triageData.respiratoryRate,
      spo2: triageData.spo2,
      nurse_notes: triageData.notes,
    };

    if (!triageData.requiresBloodSugarCheck) {
      triagePayload.assigned_doctor_type = triageData.assignedDoctorType;
    }

    const savedTriage = await submitTriage(triagePayload);

    setSuccessMessage(
      `Triage data saved for ${triageData.patient.name}. Referred to ${
        DOCTOR_TYPE_OPTIONS.find((option) => option.value === savedTriage.assigned_doctor_type)?.label || "Doctor"
      }. BMI: ${savedTriage.bmi ?? "N/A"}.`
    );
    if (triageData.requiresBloodSugarCheck) {
      setSuccessMessage(
        `Triage data saved for ${triageData.patient.name}. Patient has been sent to the Blood Sugar department. BMI: ${savedTriage.bmi ?? "N/A"}.`
      );
    }
    closeTriage();
    await refresh({ source: "after-triage" });
  }, [closeTriage, refresh]);

  return (
    <div className="triage-page">
      <div className="triage-container">
        <Header nurseName={currentUser ? currentUser.username : "Triage Nurse"} onLogout={onLogout} />
        {successMessage && <p className="queue-success">{successMessage}</p>}
        {pageError && <p className="modal-error">{pageError}</p>}
        {lastUpdated && <p className="queue-empty">Last updated: {lastUpdated.toLocaleTimeString()}</p>}
        {loading ? <p className="queue-empty">Loading triage queue...</p> : <PatientList patients={patients} onStart={openTriage} />}

        <TriageModal isOpen={modalOpen} patient={selectedPatient} onClose={closeTriage} onSubmit={handleSubmit} />
      </div>
    </div>
  );
}
