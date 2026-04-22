import { useCallback, useEffect, useMemo, useState } from "react";
import logo from "./kcf logo.jpeg";
import "./DoctorConsultationPage.css";
import {
  fetchAvailableDrugs,
  fetchPatientDetail,
  fetchQueue,
  submitDentalConsultation,
} from "./api";
import useHybridDataSync from "./useHybridDataSync";
import DrugAvailabilityPanel from "./DrugAvailabilityPanel";
import PrescriptionEditor from "./PrescriptionEditor";

const INITIAL_PRESCRIPTION = [{ inventoryId: "", drugName: "", dosage: "", quantity: "", frequency: "", status: "pending" }];
const INITIAL_FORM = {
  presentingComplaint: "",
  historyPresentingIllness: "",
  oralExamination: "",
  oralHygienePractices: "",
  pastDentalHistory: "",
  medicalHistory: "",
  diagnosis: "",
  treatmentPlan: "",
};

function Header({ clinicianName, onLogout }) {
  return (
    <header className="doc-header">
      <div className="doc-logo">
        <img src={logo} alt="KCF logo" className="site-logo" />
      </div>
      <h1>Dental Consultation</h1>
      <div className="doc-profile">
        <span>{clinicianName}</span>
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
        Start Dental Review
      </button>
    </article>
  );
}

function PatientList({ patients, onStart }) {
  return (
    <section className="doc-patient-list">
      <h2>Dental Queue</h2>
      {patients.length === 0 ? (
        <p className="doc-status-box">No patients are currently waiting for dental review.</p>
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

function SectionGuide({ children }) {
  return <p className="pediatric-section-guide">{children}</p>;
}

function DentalModal({ isOpen, patient, availableDrugs, availableDrugsLoading, onLoadAvailableDrugs, onClose, onSubmit }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [prescriptions, setPrescriptions] = useState(INITIAL_PRESCRIPTION);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setForm(INITIAL_FORM);
      setPrescriptions(INITIAL_PRESCRIPTION);
      setError("");
      setIsSubmitting(false);
    }
  }, [isOpen, patient]);

  const validPrescriptions = useMemo(
    () =>
      prescriptions.filter(
        (item) =>
          item.drugName.trim() !== "" ||
          item.dosage.trim() !== "" ||
          item.quantity.toString().trim() !== "" ||
          item.frequency.trim() !== ""
      ),
    [prescriptions]
  );

  const isPrescriptionValid = useMemo(
    () =>
      validPrescriptions.every(
        (item) =>
          item.drugName.trim() !== "" &&
          item.dosage.trim() !== "" &&
          item.quantity.toString().trim() !== "" &&
          item.frequency.trim() !== ""
      ),
    [validPrescriptions]
  );

  const hasAnyContent = useMemo(
    () => Object.values(form).some((value) => value.trim() !== "") || validPrescriptions.length > 0,
    [form, validPrescriptions.length]
  );

  const handleField = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const updatePrescriptionField = (index, field, value) => {
    setPrescriptions((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const addPrescription = () => {
    setPrescriptions((prev) => [...prev, { inventoryId: "", drugName: "", dosage: "", quantity: "", frequency: "", status: "pending" }]);
  };

  const removePrescription = (index) => {
    setPrescriptions((prev) => prev.filter((_, currentIndex) => currentIndex !== index));
  };

  const submit = (event) => {
    event.preventDefault();
    if (!hasAnyContent) {
      setError("The dental form is empty.");
      return;
    }

    if (!isPrescriptionValid) {
      setError("Complete every prescription row or clear the unfinished row.");
      return;
    }

    setError("");
    setIsSubmitting(true);

    Promise.resolve(
      onSubmit({
        patient_id: patient.id,
        presenting_complaint: form.presentingComplaint,
        history_presenting_illness: form.historyPresentingIllness,
        oral_examination: form.oralExamination,
        oral_hygiene_practices: form.oralHygienePractices,
        past_dental_history: form.pastDentalHistory,
        medical_history: form.medicalHistory,
        diagnosis: form.diagnosis,
        treatment_plan: form.treatmentPlan,
        prescriptions: validPrescriptions.map((item) => ({
          drug_name: item.drugName.trim(),
          dosage: item.dosage.trim(),
          quantity: Number(item.quantity),
          frequency: item.frequency.trim(),
          status: item.status,
        })),
      })
    )
      .catch((submitError) => setError(submitError.message))
      .finally(() => setIsSubmitting(false));
  };

  if (!isOpen || !patient) return null;

  return (
    <div className="doc-modal-overlay" onClick={onClose}>
      <div className="doc-modal" onClick={(event) => event.stopPropagation()}>
        <div className="doc-modal-header">
          <h3>Dental Consultation: {patient.name}</h3>
          <button className="close-btn" onClick={onClose}>
            x
          </button>
        </div>
        <form className="doc-modal-body" onSubmit={submit}>
          <div className="doc-section">
            <h4>Patient Details</h4>
            <div className="doc-info-grid">
              <label><span>Name</span><input value={patient.name} readOnly /></label>
              <label><span>Registration Number</span><input value={patient.reg_no} readOnly /></label>
              <label><span>Camp</span><input value={patient.camp} readOnly /></label>
              <label><span>Priority</span><input value={patient.priority} readOnly /></label>
            </div>
            <div className="doc-actions-inline">
              <button type="button" className="btn-muted" onClick={() => onLoadAvailableDrugs()}>
                Drugs Available
              </button>
            </div>
            {availableDrugsLoading && <p className="doc-status-box">Loading available drugs...</p>}
            {!availableDrugsLoading && <DrugAvailabilityPanel drugs={availableDrugs} />}
          </div>

          {patient.triage && (
            <div className="doc-section">
              <h4>Triage Vitals</h4>
              <div className="doc-info-grid">
                <label><span>Blood Pressure</span><input value={patient.triage.blood_pressure || ""} readOnly /></label>
                <label><span>Heart Rate</span><input value={patient.triage.heart_rate || ""} readOnly /></label>
                <label><span>Respiratory Rate</span><input value={patient.triage.respiratory_rate || ""} readOnly /></label>
                <label><span>SpO2</span><input value={patient.triage.spo2 || ""} readOnly /></label>
                <label><span>Temperature</span><input value={patient.triage.temperature || ""} readOnly /></label>
                <label><span>Weight</span><input value={patient.triage.weight || ""} readOnly /></label>
                <label><span>Height</span><input value={patient.triage.height || ""} readOnly /></label>
                <label><span>BMI</span><input value={patient.triage.bmi || ""} readOnly /></label>
              </div>
              <label className="pediatric-field">
                <span>Nurse Notes</span>
                <textarea rows={5} className="pediatric-writing-box" value={patient.triage.nurse_notes || ""} readOnly />
              </label>
            </div>
          )}

          <div className="doc-section">
            <h4>1. Presenting Complaint</h4>
            <SectionGuide>Describe the main dental complaint such as tooth pain, gum bleeding, swelling, sensitivity, or bad breath.</SectionGuide>
            <textarea rows={6} className="pediatric-writing-box" value={form.presentingComplaint} onChange={handleField("presentingComplaint")} />
          </div>

          <div className="doc-section">
            <h4>2. History of Presenting Illness</h4>
            <SectionGuide>Describe duration, severity, and trigger factors such as cold, heat, chewing, or touch.</SectionGuide>
            <textarea rows={6} className="pediatric-writing-box" value={form.historyPresentingIllness} onChange={handleField("historyPresentingIllness")} />
          </div>

          <div className="doc-section">
            <h4>3. Oral Examination</h4>
            <SectionGuide>Record cavities, gum condition, plaque or tartar, missing teeth, and other oral findings.</SectionGuide>
            <textarea rows={6} className="pediatric-writing-box" value={form.oralExamination} onChange={handleField("oralExamination")} />
          </div>

          <div className="doc-section">
            <h4>4. Oral Hygiene Practices</h4>
            <SectionGuide>Describe brushing frequency, toothpaste use, flossing if any, and dental visit habits.</SectionGuide>
            <textarea rows={6} className="pediatric-writing-box" value={form.oralHygienePractices} onChange={handleField("oralHygienePractices")} />
          </div>

          <div className="doc-section">
            <h4>5. Past Dental History</h4>
            <SectionGuide>Record previous extractions, fillings, surgeries, or other dental treatment.</SectionGuide>
            <textarea rows={6} className="pediatric-writing-box" value={form.pastDentalHistory} onChange={handleField("pastDentalHistory")} />
          </div>

          <div className="doc-section">
            <h4>6. Medical History</h4>
            <SectionGuide>Describe diabetes or other medical conditions that can affect oral health.</SectionGuide>
            <textarea rows={6} className="pediatric-writing-box" value={form.medicalHistory} onChange={handleField("medicalHistory")} />
          </div>

          <div className="doc-section">
            <h4>7. Diagnosis</h4>
            <SectionGuide>Enter the dental diagnosis such as dental caries, gingivitis, infection, or other findings.</SectionGuide>
            <textarea rows={5} className="pediatric-writing-box" value={form.diagnosis} onChange={handleField("diagnosis")} />
          </div>

          <div className="doc-section">
            <h4>8. Treatment Plan</h4>
            <SectionGuide>Describe medication, cleaning, extraction, referral, and follow-up advice.</SectionGuide>
            <textarea rows={6} className="pediatric-writing-box" value={form.treatmentPlan} onChange={handleField("treatmentPlan")} />
          </div>

          <div className="doc-section">
            <h4>Prescriptions</h4>
            <PrescriptionEditor
              prescriptions={prescriptions}
              availableDrugs={availableDrugs}
              updatePrescriptionField={updatePrescriptionField}
              addPrescription={addPrescription}
              removePrescription={removePrescription}
            />
          </div>

          {error && <p className="doc-error">{error}</p>}

          <div className="doc-actions">
            <button type="button" className="btn-muted" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-maroon" disabled={isSubmitting}>
              {isSubmitting ? "Submitting..." : "Submit Dental Consultation"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function DentalConsultationPage({ currentUser, onLogout }) {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [availableDrugs, setAvailableDrugs] = useState([]);
  const [availableDrugsLoading, setAvailableDrugsLoading] = useState(false);

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
      setPageError("");
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
    relevantEventTypes: ["triage_completed", "consultation_completed"],
  });

  useEffect(() => {
    refresh({ showLoading: true, source: "initial" }).catch(() => {});
  }, [refresh]);

  const openConsultation = useCallback(async (patient) => {
    setPageError("");
    setAvailableDrugs([]);
    try {
      const [detail, items] = await Promise.all([fetchPatientDetail(patient.id), fetchAvailableDrugs()]);
      setSelectedPatient(detail);
      setAvailableDrugs(items);
      setModalOpen(true);
    } catch (error) {
      setPageError(error.message);
    }
  }, []);

  const closeModal = useCallback(() => {
    setModalOpen(false);
    setSelectedPatient(null);
    setAvailableDrugs([]);
  }, []);

  const handleLoadAvailableDrugs = useCallback(async () => {
    setAvailableDrugsLoading(true);
    try {
      const items = await fetchAvailableDrugs();
      setAvailableDrugs(items);
    } catch (error) {
      setPageError(error.message);
    } finally {
      setAvailableDrugsLoading(false);
    }
  }, []);

  const handleSubmit = useCallback(async (payload) => {
    await submitDentalConsultation(payload);
    setSuccessMessage(`Dental consultation submitted for ${selectedPatient?.name || "patient"}.`);
    closeModal();
    await refresh({ source: "after-dental-consultation" });
  }, [closeModal, refresh, selectedPatient]);

  return (
    <div className="doc-page">
      <div className="doc-container">
        <Header clinicianName={currentUser ? currentUser.username : "Dentist"} onLogout={onLogout} />
        {successMessage && <p className="doc-status-success">{successMessage}</p>}
        {pageError && <p className="doc-error">{pageError}</p>}
        {lastUpdated && <p className="doc-status-box">Last updated: {lastUpdated.toLocaleTimeString()}</p>}
        {loading ? <p className="doc-status-box">Loading dental queue...</p> : <PatientList patients={patients} onStart={openConsultation} />}
        <DentalModal
          isOpen={modalOpen}
          patient={selectedPatient}
          availableDrugs={availableDrugs}
          availableDrugsLoading={availableDrugsLoading}
          onLoadAvailableDrugs={handleLoadAvailableDrugs}
          onClose={closeModal}
          onSubmit={handleSubmit}
        />
      </div>
    </div>
  );
}
