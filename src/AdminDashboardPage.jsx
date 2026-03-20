import { useEffect, useState } from "react";
import logo from "./kcf logo.jpeg";
import "./AdminDashboardPage.css";
import {
  approveUser,
  createInventory,
  fetchAdminPatients,
  fetchInventory,
  fetchPendingUsers,
  fetchReportSummary,
  fetchStageTiming,
  getReportExportUrl,
  getStoredAccessToken,
  rejectUser,
  restockInventoryItem,
} from "./api";

function Header({ currentUser, onLogout, onDownloadReport }) {
  return (
    <header className="admin-header">
      <div className="admin-logo">
        <img src={logo} alt="KCF logo" className="site-logo" />
      </div>
      <h1>Admin Dashboard</h1>
      <div className="admin-profile">
        <span>{currentUser ? currentUser.username : "Admin"}</span>
        <button className="btn-muted" onClick={onDownloadReport}>Download Report</button>
        <button className="btn-maroon" onClick={onLogout}>Logout</button>
      </div>
    </header>
  );
}

function SummaryCards({ summary }) {
  const totalPatients = summary.patients_per_camp.reduce((sum, item) => sum + item.total_patients, 0);
  const totalCamps = summary.patients_per_camp.length;
  const totalDrugs = summary.drugs_issued_per_camp.reduce((sum, item) => sum + item.total_drugs_issued, 0);

  return (
    <section className="summary-cards">
      <article className="summary-card">
        <h3>Total Patients Registered</h3>
        <p>{totalPatients}</p>
      </article>
      <article className="summary-card">
        <h3>Total Camps</h3>
        <p>{totalCamps}</p>
      </article>
      <article className="summary-card">
        <h3>Total Drugs Issued</h3>
        <p>{totalDrugs}</p>
      </article>
      <article className="summary-card">
        <h3>Completed Patients</h3>
        <p>{summary.completed_patients}</p>
      </article>
    </section>
  );
}

function PendingUsersPanel({ users, onApprove, onReject }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Pending User Approvals</h2></div>
      {users.length === 0 ? (
        <p className="admin-status-box">No pending users right now.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
                <td className="action-row">
                  <button className="btn-given" onClick={() => onApprove(user.id)}>Approve</button>
                  <button className="btn-unavailable" onClick={() => onReject(user.id)}>Reject</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

function PatientsByCamp({ items }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Patients per Camp</h2></div>
      <div className="camp-grid">
        {items.map((item) => (
          <article key={item.camp} className="camp-card">
            <h4>{item.camp}</h4>
            <p>{item.total_patients} patients</p>
            <div className="bar-wrapper"><div className="bar" style={{ width: `${Math.min((item.total_patients / 60) * 100, 100)}%` }} /></div>
          </article>
        ))}
      </div>
    </section>
  );
}

function DrugsByCamp({ items }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Drugs Issued per Camp</h2></div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Camp</th>
            <th>Total Drugs Issued</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.camp}>
              <td>{item.camp}</td>
              <td>{item.total_drugs_issued}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function AnalyticsPanel({ timing }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Stage Timing Analytics</h2></div>
      <div className="camp-grid">
        <article className="camp-card"><h4>Triage to Doctor</h4><p>{timing.average_triage_to_doctor_minutes} min</p></article>
        <article className="camp-card"><h4>Doctor to Pharmacy</h4><p>{timing.average_doctor_to_pharmacy_minutes} min</p></article>
        <article className="camp-card"><h4>Pharmacy to Complete</h4><p>{timing.average_pharmacy_to_complete_minutes} min</p></article>
        <article className="camp-card"><h4>Total Completion</h4><p>{timing.average_total_completion_minutes} min</p></article>
      </div>
    </section>
  );
}

function PatientSearchPanel({ patients, search, setSearch }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Patient Search</h2></div>
      <div className="filter-row">
        <input
          className="admin-input"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search by name, reg no, phone, village"
        />
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Reg No</th>
            <th>Name</th>
            <th>Camp</th>
            <th>Priority</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {patients.map((patient) => (
            <tr key={patient.id}>
              <td>{patient.reg_no}</td>
              <td>{patient.name}</td>
              <td>{patient.camp}</td>
              <td>{patient.priority}</td>
              <td>{patient.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function InventoryPanel({ inventory, form, setForm, onCreate, onRestock }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Inventory</h2></div>
      <div className="inventory-form">
        <input className="admin-input" placeholder="Drug name" value={form.drug_name} onChange={(event) => setForm((prev) => ({ ...prev, drug_name: event.target.value }))} />
        <input className="admin-input" placeholder="Stock quantity" type="number" min="0" value={form.stock_quantity} onChange={(event) => setForm((prev) => ({ ...prev, stock_quantity: event.target.value }))} />
        <input className="admin-input" placeholder="Reorder level" type="number" min="0" value={form.reorder_level} onChange={(event) => setForm((prev) => ({ ...prev, reorder_level: event.target.value }))} />
        <button className="btn-maroon" onClick={onCreate}>Add Drug</button>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Drug</th>
            <th>Stock</th>
            <th>Reorder Level</th>
            <th>Low Stock</th>
            <th>Restock</th>
          </tr>
        </thead>
        <tbody>
          {inventory.map((item) => (
            <tr key={item.id}>
              <td>{item.drug_name}</td>
              <td>{item.stock_quantity}</td>
              <td>{item.reorder_level}</td>
              <td>{item.is_low_stock ? "Yes" : "No"}</td>
              <td>
                <button className="btn-muted" onClick={() => onRestock(item.id)}>+10</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export default function AdminDashboardPage({ currentUser, onLogout }) {
  const [pendingUsers, setPendingUsers] = useState([]);
  const [summary, setSummary] = useState({ patients_per_camp: [], drugs_issued_per_camp: [], completed_patients: 0 });
  const [timing, setTiming] = useState({
    average_triage_to_doctor_minutes: 0,
    average_doctor_to_pharmacy_minutes: 0,
    average_pharmacy_to_complete_minutes: 0,
    average_total_completion_minutes: 0,
  });
  const [patients, setPatients] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [search, setSearch] = useState("");
  const [inventoryForm, setInventoryForm] = useState({ drug_name: "", stock_quantity: "", reorder_level: "" });
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState("");

  async function loadDashboard(searchQuery = "") {
    setError("");
    try {
      const [pending, reportSummary, stageTiming, patientList, inventoryList] = await Promise.all([
        fetchPendingUsers(),
        fetchReportSummary(),
        fetchStageTiming(),
        fetchAdminPatients(searchQuery ? `?search=${encodeURIComponent(searchQuery)}` : ""),
        fetchInventory(),
      ]);
      setPendingUsers(pending);
      setSummary(reportSummary);
      setTiming(stageTiming);
      setPatients(patientList);
      setInventory(inventoryList);
    } catch (loadError) {
      setError(loadError.message);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      loadDashboard(search);
    }, 350);
    return () => clearTimeout(timeoutId);
  }, [search]);

  const handleApprove = async (userId) => {
    try {
      await approveUser(userId);
      setStatusMessage("User approved successfully.");
      loadDashboard(search);
    } catch (actionError) {
      setError(actionError.message);
    }
  };

  const handleReject = async (userId) => {
    try {
      await rejectUser(userId);
      setStatusMessage("User rejected successfully.");
      loadDashboard(search);
    } catch (actionError) {
      setError(actionError.message);
    }
  };

  const handleCreateInventory = async () => {
    if (!inventoryForm.drug_name || !inventoryForm.stock_quantity || !inventoryForm.reorder_level) {
      setError("Fill all inventory fields.");
      return;
    }
    try {
      await createInventory({
        drug_name: inventoryForm.drug_name,
        stock_quantity: Number(inventoryForm.stock_quantity),
        reorder_level: Number(inventoryForm.reorder_level),
      });
      setInventoryForm({ drug_name: "", stock_quantity: "", reorder_level: "" });
      setStatusMessage("Inventory item created.");
      loadDashboard(search);
    } catch (actionError) {
      setError(actionError.message);
    }
  };

  const handleRestock = async (id) => {
    try {
      await restockInventoryItem(id, 10);
      setStatusMessage("Inventory restocked.");
      loadDashboard(search);
    } catch (actionError) {
      setError(actionError.message);
    }
  };

  const handleDownloadReport = () => {
    const link = document.createElement("a");
    link.href = getReportExportUrl();
    const token = getStoredAccessToken();
    if (token) {
      fetch(getReportExportUrl(), { headers: { Authorization: `Bearer ${token}` } })
        .then((response) => response.blob())
        .then((blob) => {
          const url = URL.createObjectURL(blob);
          link.href = url;
          link.download = "kwetu-care-report.doc";
          link.click();
          URL.revokeObjectURL(url);
        })
        .catch((downloadError) => setError(downloadError.message));
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-container">
        <Header currentUser={currentUser} onLogout={onLogout} onDownloadReport={handleDownloadReport} />
        {statusMessage && <p className="admin-status-success">{statusMessage}</p>}
        {error && <p className="admin-error">{error}</p>}
        <SummaryCards summary={summary} />
        <PendingUsersPanel users={pendingUsers} onApprove={handleApprove} onReject={handleReject} />
        <PatientsByCamp items={summary.patients_per_camp} />
        <DrugsByCamp items={summary.drugs_issued_per_camp} />
        <AnalyticsPanel timing={timing} />
        <PatientSearchPanel patients={patients} search={search} setSearch={setSearch} />
        <InventoryPanel
          inventory={inventory}
          form={inventoryForm}
          setForm={setInventoryForm}
          onCreate={handleCreateInventory}
          onRestock={handleRestock}
        />
      </div>
    </div>
  );
}
