import { useCallback, useEffect, useRef, useState } from "react";
import logo from "./kcf logo.jpeg";
import "./AdminDashboardPage.css";
import {
  approveUser,
  createInventory,
  downloadReport,
  fetchAdminPatients,
  fetchInventory,
  fetchPendingUsers,
  fetchReportSummary,
  rejectUser,
  restockInventoryItem,
} from "./api";
import useHybridDataSync from "./useHybridDataSync";

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

function StageQueuePanel({ counts }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Patients Waiting Per Stage</h2></div>
      <div className="camp-grid">
        <article className="camp-card"><h4>Triage</h4><p>{counts.triage || 0} waiting</p></article>
        <article className="camp-card"><h4>Doctor</h4><p>{counts.doctor || 0} waiting</p></article>
        <article className="camp-card"><h4>Pharmacy</h4><p>{counts.pharmacy || 0} waiting</p></article>
        <article className="camp-card"><h4>Complete</h4><p>{counts.complete || 0} done</p></article>
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

function InventoryPanel({ inventory, form, setForm, restockAmounts, setRestockAmounts, onCreate, onRestock }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Inventory</h2></div>
      <div className="inventory-form">
        <input className="admin-input" placeholder="Drug name" value={form.drug_name} onChange={(event) => setForm((prev) => ({ ...prev, drug_name: event.target.value }))} />
        <input className="admin-input" placeholder="Amount e.g. 400g" value={form.amount} onChange={(event) => setForm((prev) => ({ ...prev, amount: event.target.value }))} />
        <input className="admin-input" placeholder="Stock quantity" type="number" min="0" value={form.stock_quantity} onChange={(event) => setForm((prev) => ({ ...prev, stock_quantity: event.target.value }))} />
        <input className="admin-input" placeholder="Reorder level" type="number" min="0" value={form.reorder_level} onChange={(event) => setForm((prev) => ({ ...prev, reorder_level: event.target.value }))} />
        <button className="btn-maroon" onClick={onCreate}>Add Drug</button>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Drug</th>
            <th>Amount</th>
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
              <td>{item.amount}</td>
              <td>{item.stock_quantity}</td>
              <td>{item.reorder_level}</td>
              <td>{item.is_low_stock ? "Yes" : "No"}</td>
              <td className="action-row">
                <input
                  className="admin-input"
                  type="number"
                  min="1"
                  placeholder="Qty"
                  value={restockAmounts[item.id] || ""}
                  onChange={(event) =>
                    setRestockAmounts((prev) => ({ ...prev, [item.id]: event.target.value }))
                  }
                />
                <button className="btn-muted" onClick={() => onRestock(item.id)}>Restock</button>
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
  const [summary, setSummary] = useState({
    patients_per_camp: [],
    drugs_issued_per_camp: [],
    stage_waiting_counts: {},
    completed_patients: 0,
  });
  const [patients, setPatients] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [search, setSearch] = useState("");
  const [inventoryForm, setInventoryForm] = useState({ drug_name: "", amount: "", stock_quantity: "", reorder_level: "" });
  const [restockAmounts, setRestockAmounts] = useState({});
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const hasInitializedSearchRef = useRef(false);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setDebouncedSearch(search);
    }, 350);
    return () => clearTimeout(timeoutId);
  }, [search]);

  const loadDashboard = useCallback(
    async ({ showLoading = false } = {}) => {
      if (showLoading) {
        setLoading(true);
      }
      const [pending, reportSummary, patientList, inventoryList] = await Promise.all([
        fetchPendingUsers(),
        fetchReportSummary(),
        fetchAdminPatients(debouncedSearch ? `?search=${encodeURIComponent(debouncedSearch)}` : ""),
        fetchInventory(),
      ]);

      return {
        pending,
        reportSummary,
        patientList,
        inventoryList,
      };
    },
    [debouncedSearch]
  );

  const { lastUpdated, refresh } = useHybridDataSync({
    fetcher: loadDashboard,
    onData: (data, { showLoading }) => {
      setPendingUsers(data.pending);
      setSummary(data.reportSummary);
      setPatients(data.patientList);
      setInventory(data.inventoryList);
      setError("");
      if (showLoading) {
        setLoading(false);
      }
    },
    onError: (loadError, { showLoading }) => {
      setError(loadError.message);
      if (showLoading) {
        setLoading(false);
      }
    },
    relevantEventTypes: [
      "patient_created",
      "triage_completed",
      "consultation_completed",
      "prescription_updated",
      "drug_dispensed",
      "inventory_created",
      "inventory_restocked",
      "user_approved",
      "user_rejected",
    ],
  });

  useEffect(() => {
    refresh({ showLoading: true, source: "initial" }).catch(() => {});
  }, [refresh]);

  useEffect(() => {
    if (!hasInitializedSearchRef.current) {
      hasInitializedSearchRef.current = true;
      return;
    }
    refresh({ source: "search" }).catch(() => {});
  }, [debouncedSearch, refresh]);

  const handleApprove = useCallback(async (userId) => {
    try {
      await approveUser(userId);
      setStatusMessage("User approved successfully.");
      await refresh({ source: "after-approve" });
    } catch (actionError) {
      setError(actionError.message);
    }
  }, [refresh]);

  const handleReject = useCallback(async (userId) => {
    try {
      await rejectUser(userId);
      setStatusMessage("User rejected successfully.");
      await refresh({ source: "after-reject" });
    } catch (actionError) {
      setError(actionError.message);
    }
  }, [refresh]);

  const handleCreateInventory = useCallback(async () => {
    if (!inventoryForm.drug_name || !inventoryForm.amount || !inventoryForm.stock_quantity || !inventoryForm.reorder_level) {
      setError("Fill all inventory fields.");
      return;
    }
    try {
      await createInventory({
        drug_name: inventoryForm.drug_name,
        amount: inventoryForm.amount,
        stock_quantity: Number(inventoryForm.stock_quantity),
        reorder_level: Number(inventoryForm.reorder_level),
      });
      setInventoryForm({ drug_name: "", amount: "", stock_quantity: "", reorder_level: "" });
      setStatusMessage("Inventory item created.");
      await refresh({ source: "after-create-inventory" });
    } catch (actionError) {
      setError(actionError.message);
    }
  }, [inventoryForm, refresh]);

  const handleRestock = useCallback(async (id) => {
    const quantity = Number(restockAmounts[id]);
    if (!quantity || quantity < 1) {
      setError("Enter a valid restock quantity.");
      return;
    }
    try {
      await restockInventoryItem(id, quantity);
      setRestockAmounts((prev) => ({ ...prev, [id]: "" }));
      setStatusMessage("Inventory restocked.");
      await refresh({ source: "after-restock" });
    } catch (actionError) {
      setError(actionError.message);
    }
  }, [refresh, restockAmounts]);

  const handleDownloadReport = useCallback(async () => {
    try {
      await downloadReport();
    } catch (downloadError) {
      setError(downloadError.message);
    }
  }, []);

  return (
    <div className="admin-page">
      <div className="admin-container">
        <Header currentUser={currentUser} onLogout={onLogout} onDownloadReport={handleDownloadReport} />
        {statusMessage && <p className="admin-status-success">{statusMessage}</p>}
        {error && <p className="admin-error">{error}</p>}
        {lastUpdated && <p className="admin-status-box">Last updated: {lastUpdated.toLocaleTimeString()}</p>}
        {loading && <p className="admin-status-box">Loading admin dashboard...</p>}
        <SummaryCards summary={summary} />
        <PendingUsersPanel users={pendingUsers} onApprove={handleApprove} onReject={handleReject} />
        <PatientsByCamp items={summary.patients_per_camp} />
        <DrugsByCamp items={summary.drugs_issued_per_camp} />
        <StageQueuePanel counts={summary.stage_waiting_counts || {}} />
        <PatientSearchPanel patients={patients} search={search} setSearch={setSearch} />
        <InventoryPanel
          inventory={inventory}
          form={inventoryForm}
          setForm={setInventoryForm}
          restockAmounts={restockAmounts}
          setRestockAmounts={setRestockAmounts}
          onCreate={handleCreateInventory}
          onRestock={handleRestock}
        />
      </div>
    </div>
  );
}
