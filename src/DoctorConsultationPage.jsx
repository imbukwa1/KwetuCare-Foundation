import { useEffect, useMemo, useState } from "react";
import logo from "./kcf logo.jpeg";
import "./DoctorConsultationPage.css";
import { fetchPatientDetail, fetchQueue, submitConsultation } from "./api";

function Header({ doctorName, onLogout }) {
  return (
    <header className="doc-header">
      <div className="doc-logo">
        <img src={logo} alt="KCF logo" className="site-logo" />
      </div>
      <h1>Doctor</h1>
      <div className="doc-profile">
        <span>{doctorName}</span>
        <button className="btn-maroon" onClick={onLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}

function PatientCard({ patient, onStart }) {
  return (
    <article className={`doc-patient-card ${patient.priority === "urgent" ? "doc-patient-card-urgent" : ""}`}>
      <div>
        <h3>{patient.name}</h3>
        <p>ID: {patient.id}</p>
        <p>Reg No: {patient.reg_no}</p>
        <p>Camp: {patient.camp}</p>
        <p>Priority: {patient.priority}</p>
      </div>
      <button className="btn-maroon" onClick={() => onStart(patient)}>
        Start Consultation
      </button>
    </article>
  );
}

function PatientList({ patients, onStart }) {
  return (
    <section className="doc-patient-list">
      <h2>Patients List</h2>
      {patients.length === 0 ? (
        <p className="doc-status-box">No patients are currently waiting for doctor review.</p>
      ) : (
        <div className="doc-grid">
          {patients.map((patient) => (
            <PatientCard key={patient.id} patient={patient} onStart={onStart} />
          ))}
        </div>
      )}
    </section>
  );
}

function ConsultationModal({ isOpen, patient, onClose, onSubmit }) {
  const initialPrescribing = [{ drugName: "", dosage: "", quantity: "", frequency: "", status: "pending" }];
  const [doctorNotes, setDoctorNotes] = useState("");
  const [prescriptions, setPrescriptions] = useState(initialPrescribing);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const hasPatient = !!patient;

  const isPrescriptionValid = useMemo(() => {
    return prescriptions.every(
      (item) =>
        item.drugName.trim() !== "" &&
        item.dosage.trim() !== "" &&
        item.quantity.toString().trim() !== "" &&
        item.frequency.trim() !== ""
    );
  }, [prescriptions]);

  const isFormValid = hasPatient && doctorNotes.trim() !== "" && isPrescriptionValid;

  const updatePrescriptionField = (index, field, value) => {
    setPrescriptions((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const addPrescription = () => {
    setPrescriptions((prev) => [...prev, { drugName: "", dosage: "", quantity: "", frequency: "", status: "pending" }]);
  };

  const removePrescription = (index) => {
    setPrescriptions((prev) => prev.filter((_, currentIndex) => currentIndex !== index));
  };

  const submit = (event) => {
    event.preventDefault();
    if (!isFormValid) {
      setError("Please complete doctor notes and all prescriptions.");
      return;
    }

    setError("");
    setIsSubmitting(true);

    Promise.resolve(
      onSubmit({
        patient,
        doctorNotes,
        prescriptions: prescriptions.map((item) => ({
          drug_name: item.drugName,
          dosage: item.dosage,
          quantity: Number(item.quantity),
          frequency: item.frequency,
          status: item.status,
        })),
      })
    )
      .then(() => {
        setDoctorNotes("");
        setPrescriptions(initialPrescribing);
      })
      .catch((submitError) => {
        setError(submitError.message);
      })
      .finally(() => setIsSubmitting(false));
  };

  if (!isOpen || !patient) return null;

  return (
    <div className="doc-modal-overlay" onClick={onClose}>
      <div className="doc-modal" onClick={(event) => event.stopPropagation()}>
        <div className="doc-modal-header">
          <h3>Consultation: {patient.name}</h3>
          <button className="close-btn" onClick={onClose}>
            x
          </button>
        </div>
        <form className="doc-modal-body" onSubmit={submit}>
          <div className="doc-section">
            <h4>Patient Info</h4>
            <div className="doc-info-grid">
              <label>
                Name
                <input value={patient.name} readOnly />
              </label>
              <label>
                Registration Number
                <input value={patient.reg_no} readOnly />
              </label>
              <label>
                Camp
                <input value={patient.camp} readOnly />
              </label>
              <label>
                Priority
                <input value={patient.priority} readOnly />
              </label>
              {patient.guardian_name && (
                <label>
                  Guardian
                  <input value={patient.guardian_name} readOnly />
                </label>
              )}
            </div>
          </div>

          {patient.triage && (
            <div className="doc-section">
              <h4>Nurse Triage Notes</h4>
              <div className="doc-info-grid">
                <label>
                  Blood Pressure
                  <input value={patient.triage.blood_pressure || ""} readOnly />
                </label>
                <label>
                  Heart Rate
                  <input value={patient.triage.heart_rate || ""} readOnly />
                </label>
                <label>
                  Temperature
                  <input value={patient.triage.temperature || ""} readOnly />
                </label>
                <label>
                  Weight
                  <input value={patient.triage.weight || ""} readOnly />
                </label>
              </div>
              <label>
                Nurse Notes
                <textarea value={patient.triage.nurse_notes || ""} rows={3} readOnly />
              </label>
            </div>
          )}

          <div className="doc-section">
            <h4>Doctor Notes *</h4>
            <textarea
              value={doctorNotes}
              onChange={(event) => setDoctorNotes(event.target.value)}
              rows={4}
              placeholder="Enter assessment and direction"
            />
          </div>

          <div className="doc-section">
            <h4>Prescription</h4>
            {prescriptions.map((prescription, index) => (
              <div className="prescription-row" key={index}>
                <input
                  value={prescription.drugName}
                  onChange={(event) => updatePrescriptionField(index, "drugName", event.target.value)}
                  placeholder="Drug Name"
                />
                <input
                  value={prescription.dosage}
                  onChange={(event) => updatePrescriptionField(index, "dosage", event.target.value)}
                  placeholder="Dosage/Strength"
                />
                <input
                  type="number"
                  min="1"
                  value={prescription.quantity}
                  onChange={(event) => updatePrescriptionField(index, "quantity", event.target.value)}
                  placeholder="Quantity"
                />
                <select
                  value={prescription.frequency}
                  onChange={(event) => updatePrescriptionField(index, "frequency", event.target.value)}
                >
                  <option value="">Frequency</option>
                  <option value="once daily">Once daily</option>
                  <option value="twice daily">Twice daily</option>
                  <option value="three times daily">Three times daily</option>
                  <option value="as needed">As needed</option>
                </select>
                {prescriptions.length > 1 && (
                  <button type="button" className="btn-remove" onClick={() => removePrescription(index)}>
                    Remove
                  </button>
                )}
              </div>
            ))}
            <button type="button" className="btn-muted" onClick={addPrescription}>
              + Add Drug
            </button>
          </div>

          {error && <p className="doc-error">{error}</p>}

          <div className="doc-actions">
            <button type="button" className="btn-muted" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-maroon" disabled={!isFormValid || isSubmitting}>
              {isSubmitting ? "Submitting..." : "Submit Consultation"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function DoctorConsultationPage({ currentUser, onLogout }) {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [detailLoading, setDetailLoading] = useState(false);

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

  const startConsultation = async (patient) => {
    setPageError("");
    setDetailLoading(true);
    try {
      const detail = await fetchPatientDetail(patient.id);
      setSelectedPatient(detail);
      setModalOpen(true);
    } catch (error) {
      setPageError(error.message);
    } finally {
      setDetailLoading(false);
    }
  };

  const closeModal = () => {
    setModalOpen(false);
    setSelectedPatient(null);
  };

  const handleSubmit = async (data) => {
    await submitConsultation({
      patient_id: data.patient.id,
      doctor_notes: data.doctorNotes,
      prescriptions: data.prescriptions,
    });

    setPatients((prev) => prev.filter((patient) => patient.id !== data.patient.id));
    setSuccessMessage(`Consultation submitted for ${data.patient.name}.`);
    closeModal();
  };

  return (
    <div className="doc-page">
      <div className="doc-container">
        <Header doctorName={currentUser ? currentUser.username : "Doctor"} onLogout={onLogout} />
        {successMessage && <p className="doc-status-success">{successMessage}</p>}
        {pageError && <p className="doc-error">{pageError}</p>}
        {detailLoading && <p className="doc-status-box">Loading patient triage details...</p>}
        {loading ? <p className="doc-status-box">Loading doctor queue...</p> : <PatientList patients={patients} onStart={startConsultation} />}
        <ConsultationModal isOpen={modalOpen} patient={selectedPatient} onClose={closeModal} onSubmit={handleSubmit} />
      </div>
    </div>
  );
}
