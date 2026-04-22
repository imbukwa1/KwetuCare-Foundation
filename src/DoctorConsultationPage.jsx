import { useCallback, useEffect, useMemo, useState } from "react";
import logo from "./kcf logo.jpeg";
import "./DoctorConsultationPage.css";
import { fetchAvailableDrugs, fetchPatientDetail, fetchQueue, submitConsultation } from "./api";
import useHybridDataSync from "./useHybridDataSync";
import DrugAvailabilityPanel from "./DrugAvailabilityPanel";
import PrescriptionEditor from "./PrescriptionEditor";

const ROLE_LABELS = {
  general_doctor: "General Doctor",
  pediatrician: "Pediatrician",
  gynecologist: "Gynecologist",
  obstetrician: "Obstetrician",
  nutritionist: "Nutritionist",
  dental: "Dentist",
  optician: "Optician",
};

function Header({ doctorName, title, onLogout }) {
  return (
    <header className="doc-header">
      <div className="doc-logo">
        <img src={logo} alt="KCF logo" className="site-logo" />
      </div>
      <h1>{title}</h1>
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
        <p>Referred To: {ROLE_LABELS[patient.assigned_doctor_type] || patient.assigned_doctor_type}</p>
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

function ConsultationModal({ isOpen, patient, availableDrugs, availableDrugsLoading, onLoadAvailableDrugs, onClose, onSubmit }) {
  const initialPrescribing = [{ drugName: "", dosage: "", quantity: "", frequency: "", status: "pending" }];
  const initialSurgeries = [{ year: "", indication: "", surgeon: "", complications: "" }];
  const initialHospitalizations = [{ reason: "", outcome: "", year: "" }];
  
  // Health Information State
  const [selectedConditions, setSelectedConditions] = useState([]);
  const [onMedication, setOnMedication] = useState("no");
  const [medicationDetails, setMedicationDetails] = useState("");
  
  // History of Presenting Illness
  const [illnessOnset, setIllnessOnset] = useState("");
  const [illnessSeverity, setIllnessSeverity] = useState("moderate");
  const [illnessLocation, setIllnessLocation] = useState("");
  const [associatedSymptoms, setAssociatedSymptoms] = useState("");
  
  // Past Medical History
  const [chronicIllnesses, setChronicIllnesses] = useState("");
  const [surgeries, setSurgeries] = useState(initialSurgeries);
  const [hospitalizations, setHospitalizations] = useState(initialHospitalizations);
  const [significantInfections, setSignificantInfections] = useState("");
  
  // Family History
  const [familyHistory, setFamilyHistory] = useState("");
  
  // Medications and Allergies
  const [currentMedications, setCurrentMedications] = useState("");
  const [drugAllergies, setDrugAllergies] = useState("");
  const [foodAllergies, setFoodAllergies] = useState("");
  
  // Review of Systems
  const [systemsHeent, setSystemsHeent] = useState("");
  const [systemsCardiovascular, setSystemsCardiovascular] = useState("");
  const [systemsRespiratory, setSystemsRespiratory] = useState("");
  const [systemsGastrointestinal, setSystemsGastrointestinal] = useState("");
  const [systemsMusculoskeletal, setSystemsMusculoskeletal] = useState("");
  const [systemsNeurological, setSystemsNeurological] = useState("");
  
  // Diagnosis and Management
  const [diagnosis, setDiagnosis] = useState("");
  const [isReferralCase, setIsReferralCase] = useState(false);
  const [doctorNotes, setDoctorNotes] = useState("");
  const [prescriptions, setPrescriptions] = useState(initialPrescribing);
  const [recommendations, setRecommendations] = useState("");
  const [followUpInstructions, setFollowUpInstructions] = useState("");
  
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const hasPatient = !!patient;

  const resetForm = useCallback(() => {
    setSelectedConditions([]);
    setOnMedication("no");
    setMedicationDetails("");
    setIllnessOnset("");
    setIllnessSeverity("moderate");
    setIllnessLocation("");
    setAssociatedSymptoms("");
    setChronicIllnesses("");
    setSurgeries([{ year: "", indication: "", surgeon: "", complications: "" }]);
    setHospitalizations([{ reason: "", outcome: "", year: "" }]);
    setSignificantInfections("");
    setFamilyHistory("");
    setCurrentMedications("");
    setDrugAllergies("");
    setFoodAllergies("");
    setSystemsHeent("");
    setSystemsCardiovascular("");
    setSystemsRespiratory("");
    setSystemsGastrointestinal("");
    setSystemsMusculoskeletal("");
    setSystemsNeurological("");
    setDiagnosis("");
    setIsReferralCase(false);
    setDoctorNotes("");
    setPrescriptions([{ inventoryId: "", drugName: "", dosage: "", quantity: "", frequency: "", status: "pending" }]);
    setRecommendations("");
    setFollowUpInstructions("");
    setError("");
    setIsSubmitting(false);
  }, []);

  useEffect(() => {
    if (isOpen) {
      resetForm();
    }
  }, [isOpen, patient?.id, resetForm]);

  const toggleCondition = (condition) => {
    setSelectedConditions((prev) => 
      prev.includes(condition) ? prev.filter(c => c !== condition) : [...prev, condition]
    );
  };

  const updateSurgeryField = (index, field, value) => {
    setSurgeries((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const addSurgery = () => {
    setSurgeries((prev) => [...prev, { year: "", indication: "", surgeon: "", complications: "" }]);
  };

  const removeSurgery = (index) => {
    setSurgeries((prev) => prev.filter((_, currentIndex) => currentIndex !== index));
  };

  const updateHospitalizationField = (index, field, value) => {
    setHospitalizations((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const addHospitalization = () => {
    setHospitalizations((prev) => [...prev, { reason: "", outcome: "", year: "" }]);
  };

  const removeHospitalization = (index) => {
    setHospitalizations((prev) => prev.filter((_, currentIndex) => currentIndex !== index));
  };

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

  const isPrescriptionValid = useMemo(() => {
    return validPrescriptions.every(
      (item) =>
        item.drugName.trim() !== "" &&
        item.dosage.trim() !== "" &&
        item.quantity.toString().trim() !== "" &&
        item.frequency.trim() !== ""
    );
  }, [validPrescriptions]);

  const hasClinicalContent =
    diagnosis.trim() !== "" ||
    doctorNotes.trim() !== "" ||
    validPrescriptions.length > 0 ||
    associatedSymptoms.trim() !== "" ||
    illnessOnset.trim() !== "" ||
    illnessLocation.trim() !== "";

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
    if (!hasClinicalContent) {
      setError("The consultation form is empty.");
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
        patient,
        healthInformation: {
          conditions: selectedConditions,
          onMedication,
          medicationDetails,
        },
        historyOfPresentingIllness: {
          onset: illnessOnset,
          severity: illnessSeverity,
          location: illnessLocation,
          associatedSymptoms,
        },
        pastMedicalHistory: {
          chronicIllnesses,
          surgeries,
          hospitalizations,
          significantInfections,
        },
        familyHistory,
        medicationsAndAllergies: {
          currentMedications,
          drugAllergies,
          foodAllergies,
        },
        reviewOfSystems: {
          heent: systemsHeent,
          cardiovascular: systemsCardiovascular,
          respiratory: systemsRespiratory,
          gastrointestinal: systemsGastrointestinal,
          musculoskeletal: systemsMusculoskeletal,
          neurological: systemsNeurological,
        },
        diagnosis,
        isReferralCase,
        doctorNotes,
        prescriptions: validPrescriptions.map((item) => ({
          drug_name: item.drugName.trim(),
          dosage: item.dosage.trim(),
          quantity: Number(item.quantity),
          frequency: item.frequency,
          status: item.status,
        })),
        recommendations,
        followUpInstructions,
      })
    )
      .then(() => resetForm())
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
              <label>
                Referred To
                <input value={ROLE_LABELS[patient.assigned_doctor_type] || patient.assigned_doctor_type || ""} readOnly />
              </label>
              {patient.guardian_name && (
                <label>
                  Guardian
                  <input value={patient.guardian_name} readOnly />
                </label>
              )}
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
                <label>
                  Height
                  <input value={patient.triage.height || ""} readOnly />
                </label>
                <label>
                  BMI
                  <input value={patient.triage.bmi || ""} readOnly />
                </label>
                <label>
                  Respiratory Rate
                  <input value={patient.triage.respiratory_rate || ""} readOnly />
                </label>
                <label>
                  SpO2
                  <input value={patient.triage.spo2 || ""} readOnly />
                </label>
              </div>
              <label>
                Nurse Notes
                <textarea value={patient.triage.nurse_notes || ""} rows={3} readOnly />
              </label>
            </div>
          )}

          {patient.blood_sugar_check && (
            <div className="doc-section">
              <h4>Blood Sugar Check</h4>
              <div className="doc-info-grid">
                <label>
                  Blood Sugar Level
                  <input value={patient.blood_sugar_check.blood_sugar_level || ""} readOnly />
                </label>
                <label>
                  Test Type
                  <input value={patient.blood_sugar_check.test_type || ""} readOnly />
                </label>
              </div>
              <label>
                Blood Sugar Notes
                <textarea value={patient.blood_sugar_check.notes || ""} rows={3} readOnly />
              </label>
            </div>
          )}

          {/* Health Information Section */}
          <div className="doc-section">
            <h4>1. Health Information</h4>
            <div className="doc-subsection">
              <label>Select any existing health conditions:</label>
              <div className="checkbox-group">
                {["Diabetes", "Hypertension (High Blood Pressure)", "Eye Problems", "Kidney Disease", "Heart Disease"].map((condition) => (
                  <label key={condition} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={selectedConditions.includes(condition)}
                      onChange={() => toggleCondition(condition)}
                    />
                    {condition}
                  </label>
                ))}
              </div>
            </div>
            <div className="doc-subsection">
              <label>
                Are you on any medication?
                <select value={onMedication} onChange={(e) => setOnMedication(e.target.value)}>
                  <option value="no">No</option>
                  <option value="yes">Yes</option>
                </select>
              </label>
              {onMedication === "yes" && (
                <label>
                  Please specify medications:
                  <textarea
                    value={medicationDetails}
                    onChange={(e) => setMedicationDetails(e.target.value)}
                    placeholder="List medications, dosages, and frequency"
                    rows={2}
                  />
                </label>
              )}
            </div>
          </div>

          {/* History of Presenting Illness */}
          <div className="doc-section">
            <h4>2. History of Presenting Illness</h4>
            <label>
              Onset (when did symptoms start?)
              <input
                type="text"
                value={illnessOnset}
                onChange={(e) => setIllnessOnset(e.target.value)}
                placeholder="e.g., 2 weeks ago, sudden onset"
              />
            </label>
            <label>
              Severity
              <select value={illnessSeverity} onChange={(e) => setIllnessSeverity(e.target.value)}>
                <option value="mild">Mild</option>
                <option value="moderate">Moderate</option>
                <option value="severe">Severe</option>
              </select>
            </label>
            <label>
              Location
              <input
                type="text"
                value={illnessLocation}
                onChange={(e) => setIllnessLocation(e.target.value)}
                placeholder="Where does the patient feel it?"
              />
            </label>
            <label>
              Associated Symptoms
              <textarea
                value={associatedSymptoms}
                onChange={(e) => setAssociatedSymptoms(e.target.value)}
                placeholder="Detailed chronological narrative including associated symptoms"
                rows={3}
              />
            </label>
          </div>

          {/* Past Medical History */}
          <div className="doc-section">
            <h4>3. Past Medical and Surgical History</h4>
            <label>
              Chronic Illnesses
              <textarea
                value={chronicIllnesses}
                onChange={(e) => setChronicIllnesses(e.target.value)}
                placeholder="List any chronic illnesses"
                rows={2}
              />
            </label>

            <div className="doc-subsection">
              <label>Previous Surgeries/Procedures:</label>
              {surgeries.map((surgery, index) => (
                <div key={index} className="history-row">
                  <input
                    type="text"
                    value={surgery.year}
                    onChange={(e) => updateSurgeryField(index, "year", e.target.value)}
                    placeholder="Year"
                  />
                  <input
                    type="text"
                    value={surgery.indication}
                    onChange={(e) => updateSurgeryField(index, "indication", e.target.value)}
                    placeholder="Indication"
                  />
                  <input
                    type="text"
                    value={surgery.surgeon}
                    onChange={(e) => updateSurgeryField(index, "surgeon", e.target.value)}
                    placeholder="Surgeon"
                  />
                  <input
                    type="text"
                    value={surgery.complications}
                    onChange={(e) => updateSurgeryField(index, "complications", e.target.value)}
                    placeholder="Complications"
                  />
                  {surgeries.length > 1 && (
                    <button type="button" className="btn-remove" onClick={() => removeSurgery(index)}>
                      Remove
                    </button>
                  )}
                </div>
              ))}
              <button type="button" className="btn-muted" onClick={addSurgery}>
                + Add Surgery
              </button>
            </div>

            <div className="doc-subsection">
              <label>Hospitalizations:</label>
              {hospitalizations.map((hosp, index) => (
                <div key={index} className="history-row">
                  <input
                    type="text"
                    value={hosp.reason}
                    onChange={(e) => updateHospitalizationField(index, "reason", e.target.value)}
                    placeholder="Reason for hospitalization"
                  />
                  <input
                    type="text"
                    value={hosp.outcome}
                    onChange={(e) => updateHospitalizationField(index, "outcome", e.target.value)}
                    placeholder="Outcome"
                  />
                  <input
                    type="text"
                    value={hosp.year}
                    onChange={(e) => updateHospitalizationField(index, "year", e.target.value)}
                    placeholder="Year"
                  />
                  {hospitalizations.length > 1 && (
                    <button type="button" className="btn-remove" onClick={() => removeHospitalization(index)}>
                      Remove
                    </button>
                  )}
                </div>
              ))}
              <button type="button" className="btn-muted" onClick={addHospitalization}>
                + Add Hospitalization
              </button>
            </div>

            <label>
              Significant Infections
              <textarea
                value={significantInfections}
                onChange={(e) => setSignificantInfections(e.target.value)}
                placeholder="List any significant infections"
                rows={2}
              />
            </label>
          </div>

          {/* Family History */}
          <div className="doc-section">
            <h4>4. Family History</h4>
            <label>
              Any relevant family diseases or conditions
              <textarea
                value={familyHistory}
                onChange={(e) => setFamilyHistory(e.target.value)}
                placeholder="e.g., Diabetes in parents, cancer in siblings"
                rows={2}
              />
            </label>
          </div>

          {/* Medications and Allergies */}
          <div className="doc-section">
            <h4>5. Medications and Allergies</h4>
            <label>
              Current Medications
              <textarea
                value={currentMedications}
                onChange={(e) => setCurrentMedications(e.target.value)}
                placeholder="List all current medications with dosages"
                rows={2}
              />
            </label>
            <label>
              Known Drug Allergies
              <input
                type="text"
                value={drugAllergies}
                onChange={(e) => setDrugAllergies(e.target.value)}
                placeholder="List any drug allergies"
              />
            </label>
            <label>
              Known Food Allergies
              <input
                type="text"
                value={foodAllergies}
                onChange={(e) => setFoodAllergies(e.target.value)}
                placeholder="List any food allergies"
              />
            </label>
          </div>

          {/* Review of Systems */}
          <div className="doc-section">
            <h4>6. Review of Systems / Systemic Examination</h4>
            <label>
              HEENT (Head, Eyes, Ears, Nose, Throat)
              <textarea
                value={systemsHeent}
                onChange={(e) => setSystemsHeent(e.target.value)}
                placeholder="Findings and observations"
                rows={2}
              />
            </label>
            <label>
              Cardiovascular System
              <textarea
                value={systemsCardiovascular}
                onChange={(e) => setSystemsCardiovascular(e.target.value)}
                placeholder="Findings and observations"
                rows={2}
              />
            </label>
            <label>
              Respiratory System
              <textarea
                value={systemsRespiratory}
                onChange={(e) => setSystemsRespiratory(e.target.value)}
                placeholder="Findings and observations"
                rows={2}
              />
            </label>
            <label>
              Gastrointestinal
              <textarea
                value={systemsGastrointestinal}
                onChange={(e) => setSystemsGastrointestinal(e.target.value)}
                placeholder="Findings and observations"
                rows={2}
              />
            </label>
            <label>
              Musculoskeletal
              <textarea
                value={systemsMusculoskeletal}
                onChange={(e) => setSystemsMusculoskeletal(e.target.value)}
                placeholder="Findings and observations"
                rows={2}
              />
            </label>
            <label>
              Neurological
              <textarea
                value={systemsNeurological}
                onChange={(e) => setSystemsNeurological(e.target.value)}
                placeholder="Findings and observations"
                rows={2}
              />
            </label>
          </div>

          {/* Impression and Diagnosis */}
          <div className="doc-section">
            <h4>7. Impression / Diagnosis *</h4>
            <textarea
              value={diagnosis}
              onChange={(e) => setDiagnosis(e.target.value)}
              rows={2}
              placeholder="Clinical diagnosis based on findings"
            />
            <label className="checkbox-label" style={{ marginTop: "1rem" }}>
              <input
                type="checkbox"
                checked={isReferralCase}
                onChange={(event) => setIsReferralCase(event.target.checked)}
              />
              Referral Case
            </label>
          </div>

          {/* Additional Notes */}
          <div className="doc-section">
            <h4>Doctor Notes</h4>
            <textarea
              value={doctorNotes}
              onChange={(event) => setDoctorNotes(event.target.value)}
              rows={2}
              placeholder="Any additional medical notes"
            />
          </div>

          {/* Treatment and Management Plan */}
          <div className="doc-section">
            <h4>8. Treatment and Management Plan</h4>
            <label>
              Medications (Prescriptions)
              <p style={{ fontSize: "0.9em", color: "#666", marginTop: "0.5em" }}>Add all prescribed medications below:</p>
            </label>
            <PrescriptionEditor
              prescriptions={prescriptions}
              availableDrugs={availableDrugs}
              updatePrescriptionField={updatePrescriptionField}
              addPrescription={addPrescription}
              removePrescription={removePrescription}
            />

            <label style={{ marginTop: "1em" }}>
              Recommendations
              <textarea
                value={recommendations}
                onChange={(e) => setRecommendations(e.target.value)}
                placeholder="e.g., Rest, diet changes, lifestyle modifications"
                rows={2}
              />
            </label>

            <label>
              Follow-up Instructions
              <textarea
                value={followUpInstructions}
                onChange={(e) => setFollowUpInstructions(e.target.value)}
                placeholder="e.g., Return for review in 1 week, Monitor blood pressure daily"
                rows={2}
              />
            </label>
          </div>

          {error && <p className="doc-error">{error}</p>}

          <div className="doc-actions">
            <button type="button" className="btn-muted" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-maroon" disabled={isSubmitting}>
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
  const [availableDrugs, setAvailableDrugs] = useState([]);
  const [availableDrugsLoading, setAvailableDrugsLoading] = useState(false);

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

  const startConsultation = useCallback(async (patient) => {
    setPageError("");
    setDetailLoading(true);
    setAvailableDrugs([]);
    try {
      const [detail, items] = await Promise.all([fetchPatientDetail(patient.id), fetchAvailableDrugs()]);
      setSelectedPatient(detail);
      setAvailableDrugs(items);
      setModalOpen(true);
    } catch (error) {
      setPageError(error.message);
    } finally {
      setDetailLoading(false);
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

  const handleSubmit = useCallback(async (data) => {
    await submitConsultation({
      patient_id: data.patient.id,
      healthInformation: data.healthInformation,
      historyOfPresentingIllness: data.historyOfPresentingIllness,
      pastMedicalHistory: data.pastMedicalHistory,
      familyHistory: data.familyHistory,
      medicationsAndAllergies: data.medicationsAndAllergies,
      reviewOfSystems: data.reviewOfSystems,
      diagnosis: data.diagnosis,
      isReferralCase: data.isReferralCase,
      doctorNotes: data.doctorNotes,
      recommendations: data.recommendations,
      followUpInstructions: data.followUpInstructions,
      prescriptions: data.prescriptions,
    });

    setSuccessMessage(`Consultation submitted for ${data.patient.name}.`);
    closeModal();
    await refresh({ source: "after-consultation" });
  }, [closeModal, refresh]);

  return (
    <div className="doc-page">
      <div className="doc-container">
        <Header
          doctorName={currentUser ? currentUser.username : "Doctor"}
          title={ROLE_LABELS[currentUser?.role] || "Doctor"}
          onLogout={onLogout}
        />
        {successMessage && <p className="doc-status-success">{successMessage}</p>}
        {pageError && <p className="doc-error">{pageError}</p>}
        {lastUpdated && <p className="doc-status-box">Last updated: {lastUpdated.toLocaleTimeString()}</p>}
        {detailLoading && <p className="doc-status-box">Loading patient triage details...</p>}
        {loading ? <p className="doc-status-box">Loading doctor queue...</p> : <PatientList patients={patients} onStart={startConsultation} />}
        <ConsultationModal
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
