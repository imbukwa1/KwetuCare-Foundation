import { useCallback, useEffect, useMemo, useState } from "react";
import logo from "./kcf logo.jpeg";
import "./PharmacyPage.css";
import { fetchPatientDetail, fetchQueue, submitDispensing } from "./api";
import useHybridDataSync from "./useHybridDataSync";

function Header({ pharmacistName, onLogout }) {
  return (
    <header className="pharm-header">
      <div className="pharm-logo">
        <img src={logo} alt="KCF logo" className="site-logo" />
      </div>
      <h1>Pharmacy</h1>
      <div className="pharm-profile">
        <span>{pharmacistName}</span>
        <button className="btn-maroon" onClick={onLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}

function PatientCard({ patient, onGiveDrugs }) {
  return (
    <article className={`pharm-card ${patient.priority === "urgent" ? "pharm-card-urgent" : ""}`}>
      <div>
        <h3>{patient.name}</h3>
        <p>Patient ID: {patient.id}</p>
        <p>Reg No: {patient.reg_no}</p>
        <p>Camp: {patient.camp}</p>
        <p>Priority: {patient.priority}</p>
      </div>
      <button className="btn-maroon" onClick={() => onGiveDrugs(patient)}>
        Give Drugs
      </button>
    </article>
  );
}

function PatientList({ patients, onGiveDrugs }) {
  return (
    <section className="pharm-list">
      <h2>Patient List</h2>
      {patients.length === 0 ? (
        <p className="pharm-status-box">No patients are currently waiting in pharmacy.</p>
      ) : (
        <div className="pharm-grid">
          {patients.map((patient) => (
            <PatientCard key={patient.id} patient={patient} onGiveDrugs={onGiveDrugs} />
          ))}
        </div>
      )}
    </section>
  );
}

function PrescriptionTable({ prescriptionList, statusMap, onMark }) {
  return (
    <table className="pharm-table">
      <thead>
        <tr>
          <th>Drug Name</th>
          <th>Dosage</th>
          <th>Quantity</th>
          <th>Status</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        {prescriptionList.map((item) => {
          const state = statusMap[item.id] || item.status || "pending";
          return (
            <tr key={item.id} className={`row-${state}`}>
              <td>{item.drug_name}</td>
              <td>{item.dosage}</td>
              <td>{item.quantity}</td>
              <td>
                {state === "pending" && <span className="badge pending">Pending</span>}
                {state === "given" && <span className="badge given">Given</span>}
                {state === "not_available" && <span className="badge unavailable">Not Available</span>}
              </td>
              <td className="action-col">
                <button className="btn-given" onClick={() => onMark(item.id, "given")}>
                  Give
                </button>
                <button className="btn-unavailable" onClick={() => onMark(item.id, "not_available")}>
                  Unavailable
                </button>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function PharmacyModal({ isOpen, patient, onClose, onSubmit }) {
  const [statusMap, setStatusMap] = useState({});
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const prescriptionList = useMemo(() => (patient ? patient.prescriptions || [] : []), [patient]);

  const allAssigned = useMemo(() => {
    if (!patient) return false;
    return prescriptionList.every((item) => statusMap[item.id]);
  }, [patient, prescriptionList, statusMap]);

  useEffect(() => {
    setStatusMap({});
    setError("");
    setIsSubmitting(false);
  }, [patient]);

  if (!isOpen || !patient) return null;

  const changeStatus = (id, state) => {
    setStatusMap((prev) => ({ ...prev, [id]: state }));
  };

  const handleComplete = () => {
    if (!allAssigned) {
      setError("Assign a status to every prescription before completing.");
      return;
    }

    setError("");
    setIsSubmitting(true);

    Promise.resolve(
      onSubmit(patient, prescriptionList.map((item) => ({ id: item.id, status: statusMap[item.id] })))
    )
      .catch((submitError) => {
        setError(submitError.message);
      })
      .finally(() => setIsSubmitting(false));
  };

  return (
    <div className="pharm-modal-overlay" onClick={onClose}>
      <div className="pharm-modal" onClick={(event) => event.stopPropagation()}>
        <div className="pharm-modal-header">
          <h3>Dispense for {patient.name}</h3>
          <button className="close-btn" onClick={onClose}>
            x
          </button>
        </div>
        <div className="pharm-modal-body">
          <p className="pharm-subtitle">Prescriptions</p>
          <PrescriptionTable prescriptionList={prescriptionList} statusMap={statusMap} onMark={changeStatus} />
          {error && <p className="pharm-error">{error}</p>}

          <div className="pharm-modal-actions">
            <button className="btn-muted" onClick={onClose}>
              Cancel
            </button>
            <button className="btn-maroon" onClick={handleComplete} disabled={!allAssigned || isSubmitting}>
              {isSubmitting ? "Completing..." : "Complete"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function PharmacyPage({ currentUser, onLogout }) {
  const [patients, setPatients] = useState([]);
  const [selected, setSelected] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
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
    relevantEventTypes: ["consultation_completed", "prescription_updated", "drug_dispensed"],
  });

  useEffect(() => {
    refresh({ showLoading: true, source: "initial" }).catch(() => {});
  }, [refresh]);

  const openModal = useCallback(async (patient) => {
    setPageError("");
    try {
      const detail = await fetchPatientDetail(patient.id);
      setSelected(detail);
      setIsModalOpen(true);
    } catch (error) {
      setPageError(error.message);
    }
  }, []);

  const closeModal = useCallback(() => {
    setIsModalOpen(false);
    setSelected(null);
  }, []);

  const handleSubmit = useCallback(async (patient, dispensingData) => {
    await submitDispensing({
      patient_id: patient.id,
      prescriptions: dispensingData,
    });

    setSuccessMessage(`Dispensing finalized for ${patient.name}.`);
    closeModal();
    await refresh({ source: "after-dispense" });
  }, [closeModal, refresh]);

  return (
    <div className="pharm-page">
      <div className="pharm-container">
        <Header pharmacistName={currentUser ? currentUser.username : "Pharmacist"} onLogout={onLogout} />
        {successMessage && <p className="pharm-status-success">{successMessage}</p>}
        {pageError && <p className="pharm-error">{pageError}</p>}
        {lastUpdated && <p className="pharm-status-box">Last updated: {lastUpdated.toLocaleTimeString()}</p>}
        {loading ? <p className="pharm-status-box">Loading pharmacy queue...</p> : <PatientList patients={patients} onGiveDrugs={openModal} />}
        <PharmacyModal isOpen={isModalOpen} patient={selected} onClose={closeModal} onSubmit={handleSubmit} />
      </div>
    </div>
  );
}
