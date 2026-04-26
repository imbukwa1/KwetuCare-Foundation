import { useCallback, useEffect, useMemo, useState } from "react";
import logo from "./kcf logo.jpeg";
import "./TriagePage.css";
import { fetchPatientDetail, fetchQueue, submitBloodSugarCheck } from "./api";
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

function Header({ userName, onLogout }) {
  return (
    <header className="triage-header">
      <div className="triage-logo">
        <img src={logo} alt="KCF logo" className="site-logo" />
      </div>
      <h1>Blood Sugar Check</h1>
      <div className="triage-profile">
        <span>{userName}</span>
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
        <p>Reg No: {patient.reg_no}</p>
        <p>Camp: {patient.camp}</p>
        <p>Location: {patient.location}</p>
        <p>Priority: {patient.priority}</p>
      </div>
      <button className="btn-primary" onClick={() => onStart(patient)}>
        Check Blood Sugar
      </button>
    </article>
  );
}

function PatientList({ patients, onStart }) {
  return (
    <section className="patient-list">
      <h2>Patients List</h2>
      {patients.length === 0 ? (
        <p className="queue-empty">No patients are currently waiting for blood sugar check.</p>
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

function BloodSugarModal({ isOpen, patient, patientDetail, onClose, onSubmit }) {
  const [form, setForm] = useState({
    bloodSugarLevel: "",
    testType: "random",
    assignedDoctorType: "general_doctor",
    notes: "",
  });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setForm({
        bloodSugarLevel: "",
        testType: "random",
        assignedDoctorType: "general_doctor",
        notes: "",
      });
      setError("");
      setIsSubmitting(false);
    }
  }, [isOpen, patient?.id]);

  if (!isOpen || !patient) return null;

  const triage = patientDetail?.triage;

  const handleField = (field) => (event) => {
    setError("");
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const isFormValid =
    form.bloodSugarLevel.trim() !== "" &&
    form.testType.trim() !== "" &&
    form.assignedDoctorType.trim() !== "";

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!isFormValid) {
      setError("Please fill all required fields.");
      return;
    }

    setIsSubmitting(true);
    setError("");

    try {
      await onSubmit({
        patient,
        bloodSugarLevel: Number(form.bloodSugarLevel),
        testType: form.testType,
        assignedDoctorType: form.assignedDoctorType,
        notes: form.notes.trim(),
      });
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Blood Sugar Check for {patient.name}</h3>
          <button className="close-btn" onClick={onClose}>
            x
          </button>
        </div>
        <form onSubmit={handleSubmit} className="modal-form">
          <label>
            Patient Name
            <input type="text" value={patient.name} readOnly />
          </label>
          <label>
            Registration Number
            <input type="text" value={patient.reg_no} readOnly />
          </label>
          <label>
            Camp
            <input type="text" value={patient.camp} readOnly />
          </label>
          <label>
            Location
            <input type="text" value={patient.location} readOnly />
          </label>

          {triage && (
            <>
              <h4 className="doctor-section-title">Triage Handoff</h4>
              <label>
                Blood Pressure
                <input type="text" value={triage.blood_pressure || ""} readOnly />
              </label>
              <label>
                Temperature
                <input type="text" value={triage.temperature || ""} readOnly />
              </label>
              <label>
                Weight
                <input type="text" value={triage.weight || ""} readOnly />
              </label>
              <label>
                Height
                <input type="text" value={triage.height || ""} readOnly />
              </label>
              <label>
                BMI
                <input type="text" value={triage.bmi || ""} readOnly />
              </label>
              <label>
                Heart Rate
                <input type="text" value={triage.heart_rate || ""} readOnly />
              </label>
              <label>
                Respiratory Rate
                <input type="text" value={triage.respiratory_rate || ""} readOnly />
              </label>
              <label>
                SpO2
                <input type="text" value={triage.spo2 || ""} readOnly />
              </label>
              <label>
                Nurse Notes
                <textarea value={triage.nurse_notes || ""} rows={4} readOnly />
              </label>
            </>
          )}

          <h4 className="doctor-section-title">Blood Sugar Form</h4>
          <label>
            Blood Sugar Level *
            <input
              type="number"
              step="0.01"
              value={form.bloodSugarLevel}
              onChange={handleField("bloodSugarLevel")}
              placeholder="e.g. 6.40"
            />
          </label>
          <label>
            Fasting or Random *
            <select value={form.testType} onChange={handleField("testType")}>
              <option value="random">Random</option>
              <option value="fasting">Fasting</option>
            </select>
          </label>
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
          <label>
            Notes
            <textarea
              value={form.notes}
              onChange={handleField("notes")}
              rows={4}
              placeholder="Describe the blood sugar result, symptoms, timing, or any relevant observations."
            />
          </label>

          {error && <p className="modal-error">{error}</p>}
          <div className="modal-actions">
            <button type="button" className="btn-muted" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={!isFormValid || isSubmitting}>
              {isSubmitting ? "Saving..." : "Submit"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function BloodSugarPage({ currentUser, onLogout }) {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patientDetail, setPatientDetail] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [pageError, setPageError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const loadQueue = useCallback(async ({ showLoading = false } = {}) => {
    if (showLoading) {
      setLoading(true);
    }
    return fetchQueue();
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
    relevantEventTypes: ["triage_completed", "blood_sugar_checked"],
  });

  useEffect(() => {
    refresh({ showLoading: true, source: "initial" }).catch(() => {});
  }, [refresh]);

  const openCheck = useCallback(async (patient) => {
    setSelectedPatient(patient);
    setPatientDetail(null);
    setModalOpen(true);
    setDetailLoading(true);
    setPageError("");

    try {
      const detail = await fetchPatientDetail(patient.id);
      setPatientDetail(detail);
    } catch (error) {
      setPageError(error.message);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const closeCheck = useCallback(() => {
    setModalOpen(false);
    setSelectedPatient(null);
    setPatientDetail(null);
  }, []);

  const handleSubmit = useCallback(
    async (payload) => {
      const savedCheck = await submitBloodSugarCheck({
        patient_id: payload.patient.id,
        blood_sugar_level: payload.bloodSugarLevel,
        test_type: payload.testType,
        notes: payload.notes,
        assigned_doctor_type: payload.assignedDoctorType,
      });

      setSuccessMessage(
        `Blood sugar recorded for ${payload.patient.name}. Referred to ${
          DOCTOR_TYPE_OPTIONS.find((option) => option.value === savedCheck.assigned_doctor_type)?.label || "Doctor"
        }.`
      );
      closeCheck();
      await refresh({ source: "after-blood-sugar" });
    },
    [closeCheck, refresh]
  );

  const helperText = useMemo(() => {
    if (detailLoading) {
      return "Loading patient details...";
    }
    if (lastUpdated) {
      return `Last updated: ${lastUpdated.toLocaleTimeString()}`;
    }
    return "";
  }, [detailLoading, lastUpdated]);

  return (
    <div className="triage-page">
      <div className="triage-container">
        <Header userName={currentUser ? currentUser.username : "Blood Sugar"} onLogout={onLogout} />
        {successMessage && <p className="queue-success">{successMessage}</p>}
        {pageError && <p className="modal-error">{pageError}</p>}
        {helperText && <p className="queue-empty">{helperText}</p>}
        {loading ? (
          <p className="queue-empty">Loading blood sugar queue...</p>
        ) : (
          <PatientList patients={patients} onStart={openCheck} />
        )}

        <BloodSugarModal
          isOpen={modalOpen}
          patient={selectedPatient}
          patientDetail={patientDetail}
          onClose={closeCheck}
          onSubmit={handleSubmit}
        />
      </div>
    </div>
  );
}
