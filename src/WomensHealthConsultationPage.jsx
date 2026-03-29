import { useCallback, useEffect, useMemo, useState } from "react";
import logo from "./kcf logo.jpeg";
import "./DoctorConsultationPage.css";
import {
  fetchPatientDetail,
  fetchQueue,
  submitGynecologyConsultation,
  submitObstetricConsultation,
} from "./api";
import useHybridDataSync from "./useHybridDataSync";

const PAGE_CONFIG = {
  gynecologist: {
    title: "Gynecology Consultation",
    queueTitle: "Gynecology Queue",
    emptyText: "No patients are currently waiting for gynecology review.",
    actionLabel: "Start Gynecology Review",
    submitLabel: "Submit Gynecology Consultation",
    successLabel: "Gynecology consultation submitted",
    submitter: submitGynecologyConsultation,
  },
  obstetrician: {
    title: "Obstetrics Consultation",
    queueTitle: "Obstetrics Queue",
    emptyText: "No patients are currently waiting for obstetrics review.",
    actionLabel: "Start Obstetrics Review",
    submitLabel: "Submit Obstetrics Consultation",
    successLabel: "Obstetrics consultation submitted",
    submitter: submitObstetricConsultation,
  },
};

const INITIAL_PRESCRIPTION = [{ drugName: "", dosage: "", quantity: "", frequency: "", status: "pending" }];
const INITIAL_FORM = {
  presentingComplaints: "",
  historyPresentingComplaints: "",
  antenatalHistory: "",
  obstetricHistory: "",
  gynecologicalHistory: "",
  sexualReproductiveHistory: "",
  pastMedicalSurgicalFamilyHistory: "",
  examinationReviewSystems: "",
  diagnosis: "",
  treatmentPlan: "",
};

function Header({ clinicianName, title, onLogout }) {
  return (
    <header className="doc-header">
      <div className="doc-logo">
        <img src={logo} alt="KCF logo" className="site-logo" />
      </div>
      <h1>{title}</h1>
      <div className="doc-profile">
        <span>{clinicianName}</span>
        <button className="btn-maroon" onClick={onLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}

function PatientCard({ patient, onStart, actionLabel }) {
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
        {actionLabel}
      </button>
    </article>
  );
}

function PatientList({ patients, onStart, queueTitle, emptyText, actionLabel }) {
  return (
    <section className="doc-patient-list">
      <h2>{queueTitle}</h2>
      {patients.length === 0 ? (
        <p className="doc-status-box">{emptyText}</p>
      ) : (
        <div className="doc-grid">
          {patients.map((patient) => (
            <PatientCard key={patient.id} patient={patient} onStart={onStart} actionLabel={actionLabel} />
          ))}
        </div>
      )}
    </section>
  );
}

function WomensHealthModal({ isOpen, patient, onClose, onSubmit, title, submitLabel }) {
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

  const isSectionComplete = useMemo(
    () => Object.values(form).every((value) => value.trim() !== ""),
    [form]
  );

  const isPrescriptionValid = useMemo(
    () =>
      prescriptions.every(
        (item) =>
          item.drugName.trim() !== "" &&
          item.dosage.trim() !== "" &&
          item.quantity.toString().trim() !== "" &&
          item.frequency.trim() !== ""
      ),
    [prescriptions]
  );

  const isFormValid = !!patient && isSectionComplete && isPrescriptionValid;

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
    setPrescriptions((prev) => [...prev, { drugName: "", dosage: "", quantity: "", frequency: "", status: "pending" }]);
  };

  const removePrescription = (index) => {
    setPrescriptions((prev) => prev.filter((_, currentIndex) => currentIndex !== index));
  };

  const submit = (event) => {
    event.preventDefault();
    if (!isFormValid) {
      setError("Complete all consultation sections and prescriptions.");
      return;
    }

    setError("");
    setIsSubmitting(true);

    Promise.resolve(
      onSubmit({
        patient_id: patient.id,
        presenting_complaints: form.presentingComplaints,
        history_presenting_complaints: form.historyPresentingComplaints,
        antenatal_history: form.antenatalHistory,
        obstetric_history: form.obstetricHistory,
        gynecological_history: form.gynecologicalHistory,
        sexual_reproductive_history: form.sexualReproductiveHistory,
        past_medical_surgical_family_history: form.pastMedicalSurgicalFamilyHistory,
        examination_review_systems: form.examinationReviewSystems,
        diagnosis: form.diagnosis,
        treatment_plan: form.treatmentPlan,
        prescriptions: prescriptions.map((item) => ({
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
          <h3>{title}: {patient.name}</h3>
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
            </div>
          </div>

          {patient.triage && (
            <div className="doc-section">
              <h4>Nurse Triage Notes</h4>
              <div className="doc-info-grid">
                <label><span>Blood Pressure</span><input value={patient.triage.blood_pressure || ""} readOnly /></label>
                <label><span>Heart Rate</span><input value={patient.triage.heart_rate || ""} readOnly /></label>
                <label><span>Temperature</span><input value={patient.triage.temperature || ""} readOnly /></label>
                <label><span>Weight</span><input value={patient.triage.weight || ""} readOnly /></label>
                <label><span>Height</span><input value={patient.triage.height || ""} readOnly /></label>
                <label><span>BMI</span><input value={patient.triage.bmi || ""} readOnly /></label>
                <label><span>Respiratory Rate</span><input value={patient.triage.respiratory_rate || ""} readOnly /></label>
                <label><span>SpO2</span><input value={patient.triage.spo2 || ""} readOnly /></label>
              </div>
              <label className="pediatric-field">
                <span>Nurse Notes</span>
                <textarea rows={4} className="pediatric-writing-box" value={patient.triage.nurse_notes || ""} readOnly />
              </label>
            </div>
          )}

          <div className="doc-section">
            <h4>1. Presenting Complaints</h4>
            <p className="pediatric-section-guide">Describe the main complaints in detail.</p>
            <textarea rows={6} className="pediatric-writing-box" value={form.presentingComplaints} onChange={handleField("presentingComplaints")} />
          </div>

          <div className="doc-section">
            <h4>2. History of Presenting Complaints</h4>
            <p className="pediatric-section-guide">Include bleeding, discharge, fever, urinary or bowel symptoms, and how the condition affects daily activities.</p>
            <textarea rows={7} className="pediatric-writing-box" value={form.historyPresentingComplaints} onChange={handleField("historyPresentingComplaints")} />
          </div>

          <div className="doc-section">
            <h4>3. Antenatal History</h4>
            <p className="pediatric-section-guide">Describe ANC attendance frequency, ANC profile details, and supplements issued.</p>
            <textarea rows={6} className="pediatric-writing-box" value={form.antenatalHistory} onChange={handleField("antenatalHistory")} />
          </div>

          <div className="doc-section">
            <h4>4. Obstetric History</h4>
            <p className="pediatric-section-guide">Include gravida, para, abortions, living children, previous pregnancies, mode of delivery, and complications.</p>
            <textarea rows={7} className="pediatric-writing-box" value={form.obstetricHistory} onChange={handleField("obstetricHistory")} />
          </div>

          <div className="doc-section">
            <h4>5. Gynecological History</h4>
            <p className="pediatric-section-guide">Describe menarche, menstrual cycle, contraceptive history, and any previous gynecological procedures or surgeries.</p>
            <textarea rows={7} className="pediatric-writing-box" value={form.gynecologicalHistory} onChange={handleField("gynecologicalHistory")} />
          </div>

          <div className="doc-section">
            <h4>6. Sexual and Reproductive History</h4>
            <p className="pediatric-section-guide">Include age at sexual debut, number of partners, STI history, and infertility history where relevant.</p>
            <textarea rows={6} className="pediatric-writing-box" value={form.sexualReproductiveHistory} onChange={handleField("sexualReproductiveHistory")} />
          </div>

          <div className="doc-section">
            <h4>7. Past Medical, Surgical, and Family History</h4>
            <p className="pediatric-section-guide">Describe chronic illnesses, previous surgeries, and important family medical history.</p>
            <textarea rows={6} className="pediatric-writing-box" value={form.pastMedicalSurgicalFamilyHistory} onChange={handleField("pastMedicalSurgicalFamilyHistory")} />
          </div>

          <div className="doc-section">
            <h4>8. Examination and Review of Systems</h4>
            <p className="pediatric-section-guide">Write the head-to-toe examination findings and system-based observations.</p>
            <textarea rows={7} className="pediatric-writing-box" value={form.examinationReviewSystems} onChange={handleField("examinationReviewSystems")} />
          </div>

          <div className="doc-section">
            <h4>9. Impression / Diagnosis</h4>
            <p className="pediatric-section-guide">Enter the clinical impression or diagnosis based on the findings.</p>
            <textarea rows={5} className="pediatric-writing-box" value={form.diagnosis} onChange={handleField("diagnosis")} />
          </div>

          <div className="doc-section">
            <h4>10. Treatment Plan / Action Plan</h4>
            <p className="pediatric-section-guide">Describe medications, procedures, and follow-up instructions.</p>
            <textarea rows={6} className="pediatric-writing-box" value={form.treatmentPlan} onChange={handleField("treatmentPlan")} />
          </div>

          <div className="doc-section">
            <h4>Prescriptions</h4>
            {prescriptions.map((prescription, index) => (
              <div className="prescription-row" key={index}>
                <input value={prescription.drugName} onChange={(event) => updatePrescriptionField(index, "drugName", event.target.value)} placeholder="Drug Name" />
                <input value={prescription.dosage} onChange={(event) => updatePrescriptionField(index, "dosage", event.target.value)} placeholder="Dosage/Strength" />
                <input type="number" min="1" value={prescription.quantity} onChange={(event) => updatePrescriptionField(index, "quantity", event.target.value)} placeholder="Quantity" />
                <select value={prescription.frequency} onChange={(event) => updatePrescriptionField(index, "frequency", event.target.value)}>
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
              {isSubmitting ? "Submitting..." : submitLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function WomensHealthConsultationPage({ currentUser, onLogout, role }) {
  const config = PAGE_CONFIG[role];
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
    try {
      const detail = await fetchPatientDetail(patient.id);
      setSelectedPatient(detail);
      setModalOpen(true);
    } catch (error) {
      setPageError(error.message);
    }
  }, []);

  const closeModal = useCallback(() => {
    setModalOpen(false);
    setSelectedPatient(null);
  }, []);

  const handleSubmit = useCallback(async (payload) => {
    await config.submitter(payload);
    setSuccessMessage(`${config.successLabel} for ${selectedPatient?.name || "patient"}.`);
    closeModal();
    await refresh({ source: `after-${role}-consultation` });
  }, [closeModal, config, refresh, role, selectedPatient]);

  return (
    <div className="doc-page">
      <div className="doc-container">
        <Header clinicianName={currentUser ? currentUser.username : config.title} title={config.title} onLogout={onLogout} />
        {successMessage && <p className="doc-status-success">{successMessage}</p>}
        {pageError && <p className="doc-error">{pageError}</p>}
        {lastUpdated && <p className="doc-status-box">Last updated: {lastUpdated.toLocaleTimeString()}</p>}
        {loading ? (
          <p className="doc-status-box">Loading specialist queue...</p>
        ) : (
          <PatientList patients={patients} onStart={openConsultation} queueTitle={config.queueTitle} emptyText={config.emptyText} actionLabel={config.actionLabel} />
        )}
        <WomensHealthModal
          isOpen={modalOpen}
          patient={selectedPatient}
          onClose={closeModal}
          onSubmit={handleSubmit}
          title={config.title}
          submitLabel={config.submitLabel}
        />
      </div>
    </div>
  );
}
