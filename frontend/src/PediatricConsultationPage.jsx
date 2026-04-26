import { useCallback, useEffect, useMemo, useState } from "react";
import logo from "./kcf logo.jpeg";
import "./DoctorConsultationPage.css";
import { fetchAvailableDrugs, fetchPatientDetail, fetchQueue, submitPediatricConsultation } from "./api";
import useHybridDataSync from "./useHybridDataSync";
import DrugAvailabilityPanel from "./DrugAvailabilityPanel";
import PrescriptionEditor from "./PrescriptionEditor";

function Header({ doctorName, onLogout }) {
  return (
    <header className="doc-header">
      <div className="doc-logo">
        <img src={logo} alt="KCF logo" className="site-logo" />
      </div>
      <h1>Pediatric Consultation</h1>
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
        Start Pediatric Review
      </button>
    </article>
  );
}

function PatientList({ patients, onStart }) {
  return (
    <section className="doc-patient-list">
      <h2>Pediatric Queue</h2>
      {patients.length === 0 ? (
        <p className="doc-status-box">No patients are currently waiting for pediatric review.</p>
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

const INITIAL_PRESCRIPTION = [{ inventoryId: "", drugName: "", dosage: "", quantity: "", frequency: "", status: "pending" }];
const INITIAL_FORM = {
  presentingComplaint: "",
  historyPresentingIllness: "",
  pastMedicalHistory: "",
  prenatalAntenatalHistory: "",
  familySocialHistory: "",
  diagnosis: "",
};
const INITIAL_BIRTH_DETAILS = {
  placeOfBirth: "",
  gestationalAge: "",
  birthWeight: "",
  firstCry: "",
  complications: "",
};
const INITIAL_NUTRITION_DETAILS = {
  exclusiveBreastfeedingDuration: "",
  weaningAge: "",
  appetiteDescription: "",
};
const INITIAL_GROWTH_DETAILS = {
  heightProgression: "",
  weightProgression: "",
  developmentalMilestones: "",
};

function CheckboxRow({ label, options, value, onChange }) {
  return (
    <div className="pediatric-check-row">
      <span className="pediatric-check-label">{label}</span>
      <div className="pediatric-check-options">
        {options.map((option) => (
          <label key={option.value} className={`pediatric-check-option ${value === option.value ? "pediatric-check-option-active" : ""}`}>
            <input
              type="checkbox"
              checked={value === option.value}
              onChange={() => onChange(value === option.value ? "" : option.value)}
            />
            <span>{option.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

function SectionGuide({ children }) {
  return <p className="pediatric-section-guide">{children}</p>;
}

function PediatricModal({ isOpen, patient, availableDrugs, availableDrugsLoading, onLoadAvailableDrugs, onClose, onSubmit }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [birthDetails, setBirthDetails] = useState(INITIAL_BIRTH_DETAILS);
  const [nutritionDetails, setNutritionDetails] = useState(INITIAL_NUTRITION_DETAILS);
  const [growthDetails, setGrowthDetails] = useState(INITIAL_GROWTH_DETAILS);
  const [prescriptions, setPrescriptions] = useState(INITIAL_PRESCRIPTION);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setForm(INITIAL_FORM);
      setBirthDetails(INITIAL_BIRTH_DETAILS);
      setNutritionDetails(INITIAL_NUTRITION_DETAILS);
      setGrowthDetails(INITIAL_GROWTH_DETAILS);
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

  const hasAnyContent = useMemo(() => {
    const textSections = [...Object.values(form), ...Object.values(birthDetails), ...Object.values(nutritionDetails), ...Object.values(growthDetails)];
    return textSections.some((value) => String(value).trim() !== "") || validPrescriptions.length > 0;
  }, [birthDetails, form, growthDetails, nutritionDetails, validPrescriptions.length]);

  const handleField = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleBirthField = (field) => (valueOrEvent) => {
    const value = typeof valueOrEvent === "string" ? valueOrEvent : valueOrEvent.target.value;
    setBirthDetails((prev) => ({ ...prev, [field]: value }));
  };

  const handleNutritionField = (field) => (event) => {
    setNutritionDetails((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleGrowthField = (field) => (event) => {
    setGrowthDetails((prev) => ({ ...prev, [field]: event.target.value }));
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
      setError("The pediatric form is empty.");
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
        past_medical_history: form.pastMedicalHistory,
        prenatal_antenatal_history: form.prenatalAntenatalHistory,
        birth_history: [
          `Place of birth: ${birthDetails.placeOfBirth}`,
          `Gestational age: ${birthDetails.gestationalAge}`,
          `Birth weight: ${birthDetails.birthWeight}`,
          `First cry: ${birthDetails.firstCry}`,
          `Complications either mother/child: ${birthDetails.complications}`,
        ].join("\n"),
        nutritional_history: [
          `Duration of exclusive breastfeeding: ${nutritionDetails.exclusiveBreastfeedingDuration}`,
          `Age of weaning: ${nutritionDetails.weaningAge}`,
          `Appetite description: ${nutritionDetails.appetiteDescription}`,
        ].join("\n"),
        growth_development_history: [
          `Height progression: ${growthDetails.heightProgression}`,
          `Weight progression: ${growthDetails.weightProgression}`,
          `Developmental milestones: ${growthDetails.developmentalMilestones}`,
        ].join("\n"),
        family_social_history: form.familySocialHistory,
        diagnosis: form.diagnosis,
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
          <h3>Pediatric Consultation: {patient.name}</h3>
          <button className="close-btn" onClick={onClose}>
            x
          </button>
        </div>
        <form className="doc-modal-body" onSubmit={submit}>
          <div className="doc-section">
            <h4>Patient Details</h4>
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
                <label>
                  Blood Pressure
                  <input value={patient.triage.blood_pressure || ""} readOnly />
                </label>
                <label>
                  Heart Rate
                  <input value={patient.triage.heart_rate || ""} readOnly />
                </label>
                <label>
                  Respiratory Rate
                  <input value={patient.triage.respiratory_rate || ""} readOnly />
                </label>
                <label>
                  SpO2
                  <input value={patient.triage.spo2 || ""} readOnly />
                </label>
                <label>
                  Temperature
                  <input value={patient.triage.temperature || ""} readOnly />
                </label>
                <label>
                  Weight
                  <input value={patient.triage.weight || ""} readOnly />
                </label>
                <label>
                  Height
                  <input value={patient.triage.height || ""} readOnly />
                </label>
                <label>
                  BMI
                  <input value={patient.triage.bmi || ""} readOnly />
                </label>
              </div>
              <label className="pediatric-field">
                <span>Nurse Notes</span>
                <textarea
                  rows={5}
                  className="pediatric-writing-box"
                  value={patient.triage.nurse_notes || ""}
                  readOnly
                />
              </label>
            </div>
          )}

          <div className="doc-section">
            <h4>1. Presenting Complaint / Chief Complaint</h4>
            <SectionGuide>Describe the main complaint(s), the duration of the complaint, and list them from oldest to most recent if there is more than one.</SectionGuide>
            <textarea
              rows={7}
              className="pediatric-writing-box"
              value={form.presentingComplaint}
              onChange={handleField("presentingComplaint")}
              placeholder="Write the presenting complaint(s) here..."
            />
          </div>

          <div className="doc-section">
            <h4>2. History of Presenting Illness</h4>
            <SectionGuide>Describe the illness in chronological order. Include feeding, activity, sleep, temperament, treatment already given, whether the child is improving or worsening, and any risk factors such as family history.</SectionGuide>
            <textarea
              rows={8}
              className="pediatric-writing-box"
              value={form.historyPresentingIllness}
              onChange={handleField("historyPresentingIllness")}
              placeholder="Write the history of presenting illness here..."
            />
          </div>

          <div className="doc-section">
            <h4>3. Past Medical History</h4>
            <SectionGuide>Describe previous illnesses, chronic conditions, previous admissions, surgeries, and hospitalizations.</SectionGuide>
            <textarea
              rows={6}
              className="pediatric-writing-box"
              value={form.pastMedicalHistory}
              onChange={handleField("pastMedicalHistory")}
              placeholder="Write the past medical history here..."
            />
          </div>

          <div className="doc-section">
            <h4>4. Pre-natal / Ante-natal History</h4>
            <SectionGuide>Describe when the mother started clinic, how often she attended, vaccines received, complications during pregnancy, and any drugs or substances used including alcohol or tobacco.</SectionGuide>
            <textarea
              rows={7}
              className="pediatric-writing-box"
              value={form.prenatalAntenatalHistory}
              onChange={handleField("prenatalAntenatalHistory")}
              placeholder="Write the pre-natal / ante-natal history here..."
            />
          </div>

          <div className="doc-section">
            <h4>5. Birth History</h4>
            <SectionGuide>Select the birth details below, then describe any complications affecting the mother or child.</SectionGuide>
            <CheckboxRow
              label="Place of Birth"
              value={birthDetails.placeOfBirth}
              onChange={handleBirthField("placeOfBirth")}
              options={[
                { value: "Home", label: "Home" },
                { value: "Hospital", label: "Hospital" },
                { value: "Clinic", label: "Clinic" },
              ]}
            />
            <CheckboxRow
              label="Gestational Age"
              value={birthDetails.gestationalAge}
              onChange={handleBirthField("gestationalAge")}
              options={[
                { value: "Term", label: "Term" },
                { value: "Pre-term", label: "Pre-term" },
                { value: "Post-term", label: "Post-term" },
              ]}
            />
            <div className="pediatric-mini-grid">
              <label className="pediatric-field">
                <span>Describe the birth weight.</span>
                <input
                  value={birthDetails.birthWeight}
                  onChange={handleBirthField("birthWeight")}
                  placeholder="e.g. 3.2 kg"
                />
              </label>
            </div>
            <CheckboxRow
              label="First Cry"
              value={birthDetails.firstCry}
              onChange={handleBirthField("firstCry")}
              options={[
                { value: "Immediate", label: "Immediate" },
                { value: "Delayed", label: "Delayed" },
              ]}
            />
            <label className="pediatric-field">
              <span>Describe complications either in the mother or the child.</span>
              <textarea
                rows={5}
                className="pediatric-writing-box"
                value={birthDetails.complications}
                onChange={handleBirthField("complications")}
                placeholder="Write the birth complications here..."
              />
            </label>
          </div>

          <div className="doc-section">
            <h4>6. Nutritional History</h4>
            <SectionGuide>Fill in the feeding history below, then describe appetite and any nutritional concerns.</SectionGuide>
            <div className="pediatric-mini-grid pediatric-mini-grid-two">
              <label className="pediatric-field">
                <span>Describe the duration of exclusive breastfeeding.</span>
                <input
                  value={nutritionDetails.exclusiveBreastfeedingDuration}
                  onChange={handleNutritionField("exclusiveBreastfeedingDuration")}
                  placeholder="e.g. 6 months"
                />
              </label>
              <label className="pediatric-field">
                <span>Describe the age of weaning.</span>
                <input
                  value={nutritionDetails.weaningAge}
                  onChange={handleNutritionField("weaningAge")}
                  placeholder="e.g. 7 months"
                />
              </label>
            </div>
            <label className="pediatric-field">
              <span>Describe the child's appetite.</span>
              <textarea
                rows={5}
                className="pediatric-writing-box"
                value={nutritionDetails.appetiteDescription}
                onChange={handleNutritionField("appetiteDescription")}
                placeholder="Write the nutritional history here..."
              />
            </label>
          </div>

          <div className="doc-section">
            <h4>7. Growth and Development History</h4>
            <SectionGuide>Describe the child's growth pattern and developmental milestones.</SectionGuide>
            <div className="pediatric-mini-grid pediatric-mini-grid-two">
              <label className="pediatric-field">
                <span>Describe height progression.</span>
                <input
                  value={growthDetails.heightProgression}
                  onChange={handleGrowthField("heightProgression")}
                  placeholder="Describe height progression"
                />
              </label>
              <label className="pediatric-field">
                <span>Describe weight progression.</span>
                <input
                  value={growthDetails.weightProgression}
                  onChange={handleGrowthField("weightProgression")}
                  placeholder="Describe weight progression"
                />
              </label>
            </div>
            <label className="pediatric-field">
              <span>Describe developmental milestones.</span>
              <textarea
                rows={5}
                className="pediatric-writing-box"
                value={growthDetails.developmentalMilestones}
                onChange={handleGrowthField("developmentalMilestones")}
                placeholder="Write the developmental milestones here..."
              />
            </label>
          </div>

          <div className="doc-section">
            <h4>8. Family and Social History</h4>
            <SectionGuide>Describe family diseases, living conditions, and social factors that may affect the child's health.</SectionGuide>
            <textarea
              rows={7}
              className="pediatric-writing-box"
              value={form.familySocialHistory}
              onChange={handleField("familySocialHistory")}
              placeholder="Write the family and social history here..."
            />
          </div>

          <div className="doc-section">
            <h4>9. Diagnosis</h4>
            <SectionGuide>Describe the working diagnosis, differential diagnosis, or final diagnosis based on the pediatric review.</SectionGuide>
            <textarea
              rows={6}
              className="pediatric-writing-box"
              value={form.diagnosis}
              onChange={handleField("diagnosis")}
              placeholder="Write the diagnosis here..."
            />
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
              {isSubmitting ? "Submitting..." : "Submit Pediatric Consultation"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function PediatricConsultationPage({ currentUser, onLogout }) {
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

  const handleSubmit = useCallback(
    async (payload) => {
      await submitPediatricConsultation(payload);
      setSuccessMessage(`Pediatric consultation submitted for ${selectedPatient?.name || "patient"}.`);
      closeModal();
      await refresh({ source: "after-pediatric-consultation" });
    },
    [closeModal, refresh, selectedPatient]
  );

  return (
    <div className="doc-page">
      <div className="doc-container">
        <Header doctorName={currentUser ? currentUser.username : "Pediatrician"} onLogout={onLogout} />
        {successMessage && <p className="doc-status-success">{successMessage}</p>}
        {pageError && <p className="doc-error">{pageError}</p>}
        {lastUpdated && <p className="doc-status-box">Last updated: {lastUpdated.toLocaleTimeString()}</p>}
        {loading ? <p className="doc-status-box">Loading pediatric queue...</p> : <PatientList patients={patients} onStart={openConsultation} />}
        <PediatricModal
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
