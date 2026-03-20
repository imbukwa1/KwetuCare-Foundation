import { useEffect, useMemo, useState } from "react";
import logo from "./kcf logo.jpeg";
import "./TriagePage.css";
import { fetchQueue, submitTriage } from "./api";

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
  const [form, setForm] = useState({ bloodPressure: "", heartRate: "", temperature: "", weight: "", notes: "" });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isFormValid = useMemo(() => {
    return (
      form.bloodPressure.trim() !== "" &&
      form.heartRate.trim() !== "" &&
      form.temperature.trim() !== "" &&
      form.weight.trim() !== ""
    );
  }, [form]);

  const handleField = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
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
        heartRate: Number(form.heartRate),
        temperature: Number(form.temperature),
        weight: Number(form.weight),
        notes: form.notes,
      })
    )
      .then(() => {
        setForm({ bloodPressure: "", heartRate: "", temperature: "", weight: "", notes: "" });
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
          <label>
            Heart Rate (bpm) *
            <input type="number" value={form.heartRate} onChange={handleField("heartRate")} placeholder="e.g. 82" />
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

  useEffect(() => {
    async function loadQueue() {
      setLoading(true);
      setPageError("");
      try {
        const queue = await fetchQueue();
        setPatients(queue);
      } catch (error) {
        setPageError(error.message);
      } finally {
        setLoading(false);
      }
    }

    loadQueue();
  }, []);

  const openTriage = (patient) => {
    setSelectedPatient(patient);
    setModalOpen(true);
  };

  const closeTriage = () => {
    setModalOpen(false);
    setSelectedPatient(null);
  };

  const handleSubmit = async (triageData) => {
    await submitTriage({
      patient_id: triageData.patient.id,
      blood_pressure: triageData.bloodPressure,
      temperature: triageData.temperature,
      weight: triageData.weight,
      heart_rate: triageData.heartRate,
      nurse_notes: triageData.notes,
    });

    setPatients((prev) => prev.filter((patient) => patient.id !== triageData.patient.id));
    setSuccessMessage(`Triage data saved for ${triageData.patient.name}.`);
    closeTriage();
  };

  return (
    <div className="triage-page">
      <div className="triage-container">
        <Header nurseName={currentUser ? currentUser.username : "Triage Nurse"} onLogout={onLogout} />
        {successMessage && <p className="queue-success">{successMessage}</p>}
        {pageError && <p className="modal-error">{pageError}</p>}
        {loading ? <p className="queue-empty">Loading triage queue...</p> : <PatientList patients={patients} onStart={openTriage} />}

        <TriageModal isOpen={modalOpen} patient={selectedPatient} onClose={closeTriage} onSubmit={handleSubmit} />
      </div>
    </div>
  );
}
