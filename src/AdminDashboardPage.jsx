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

const REPORT_PERIOD_OPTIONS = [
  { value: "1m", label: "Last 1 Month" },
  { value: "3m", label: "Last 3 Months" },
  { value: "1y", label: "Last 1 Year" },
];

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
        <article className="camp-card"><h4>Blood Sugar</h4><p>{counts.blood_sugar || 0} waiting</p></article>
        <article className="camp-card"><h4>Doctor</h4><p>{counts.doctor || 0} waiting</p></article>
        <article className="camp-card"><h4>Pharmacy</h4><p>{counts.pharmacy || 0} waiting</p></article>
        <article className="camp-card"><h4>Complete</h4><p>{counts.complete || 0} done</p></article>
      </div>
    </section>
  );
}

function ReportControls({ reportPeriod, setReportPeriod }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Report Range</h2></div>
      <div className="filter-row">
        <select className="admin-input" value={reportPeriod} onChange={(event) => setReportPeriod(event.target.value)}>
          {REPORT_PERIOD_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    </section>
  );
}

function OutcomePanel({ summary, referralCases }) {
  return (
    <section className="summary-cards">
      <article className="summary-card">
        <h3>Treated</h3>
        <p>{summary.treated || 0}</p>
      </article>
      <article className="summary-card">
        <h3>Referred</h3>
        <p>{referralCases || 0}</p>
      </article>
      <article className="summary-card">
        <h3>Pending</h3>
        <p>{summary.pending || 0}</p>
      </article>
    </section>
  );
}

function DrugUsagePanel({ items }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Drug Usage Analytics</h2></div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Drug</th>
            <th>Amount</th>
            <th>Total Quantity</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={`${item.drug_name}-${item.amount}`}>
              <td>{item.drug_name}</td>
              <td>{item.amount}</td>
              <td>{item.total_quantity}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function DiagnosisDistributionPanel({ items }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Disease Distribution per Camp</h2></div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Camp</th>
            <th>Condition</th>
            <th>Patients</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
            <tr key={`${item.camp}-${item.condition}-${index}`}>
              <td>{item.camp}</td>
              <td>{item.condition}</td>
              <td>{item.total_cases}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function CommonConditionsPanel({ items }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Most Common Conditions</h2></div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Condition</th>
            <th>Total Cases</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.condition}>
              <td>{item.condition}</td>
              <td>{item.total_cases}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function DrugTrendPanel({ items }) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Drug Usage Trends</h2></div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Period</th>
            <th>Total Quantity Dispensed</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.period}>
              <td>{item.period}</td>
              <td>{item.total_quantity}</td>
            </tr>
          ))}
        </tbody>
      </table>
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
          placeholder="Search by name, reg no, phone, location"
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
        <input className="admin-input" placeholder="Unit/Dosage e.g. 500mg" value={form.amount} onChange={(event) => setForm((prev) => ({ ...prev, amount: event.target.value }))} />
        <input className="admin-input" placeholder="Batch quantity" type="number" min="1" value={form.stock_quantity} onChange={(event) => setForm((prev) => ({ ...prev, stock_quantity: event.target.value }))} />
        <input className="admin-input" placeholder="Reorder level" type="number" min="0" value={form.reorder_level} onChange={(event) => setForm((prev) => ({ ...prev, reorder_level: event.target.value }))} />
        <input className="admin-input" type="date" value={form.expiry_date} onChange={(event) => setForm((prev) => ({ ...prev, expiry_date: event.target.value }))} />
        <button className="btn-maroon" onClick={onCreate}>Add Batch</button>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Drug</th>
            <th>Amount</th>
            <th>Available Stock</th>
            <th>Reorder Level</th>
            <th>Expiry Alerts</th>
            <th>Batches</th>
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
              <td>
                {item.expired_batch_count > 0 && <div>Expired: {item.expired_batch_count}</div>}
                {item.near_expiry_batch_count > 0 && <div>Near expiry: {item.near_expiry_batch_count}</div>}
                {item.expired_batch_count === 0 && item.near_expiry_batch_count === 0 && "Clear"}
                {item.is_low_stock && <div>Low stock</div>}
              </td>
              <td>
                {item.batches?.length ? (
                  item.batches.map((batch) => (
                    <div key={batch.id}>
                      {batch.quantity_remaining}/{batch.quantity_received} exp {batch.expiry_date} ({batch.status})
                    </div>
                  ))
                ) : (
                  "No batches"
                )}
              </td>
              <td className="action-row">
                <input
                  className="admin-input"
                  type="number"
                  min="1"
                  placeholder="Qty"
                  value={restockAmounts[item.id]?.quantity || ""}
                  onChange={(event) =>
                    setRestockAmounts((prev) => ({
                      ...prev,
                      [item.id]: { ...(prev[item.id] || {}), quantity: event.target.value },
                    }))
                  }
                />
                <input
                  className="admin-input"
                  type="date"
                  value={restockAmounts[item.id]?.expiry_date || ""}
                  onChange={(event) =>
                    setRestockAmounts((prev) => ({
                      ...prev,
                      [item.id]: { ...(prev[item.id] || {}), expiry_date: event.target.value },
                    }))
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
    period_label: "Last 1 Month",
    patients_per_camp: [],
    drugs_issued_per_camp: [],
    drug_usage_by_name: [],
    diagnosis_distribution_per_camp: [],
    most_common_conditions: [],
    drug_usage_trends: [],
    stage_waiting_counts: {},
    completed_patients: 0,
    referral_cases: 0,
    outcome_summary: { treated: 0, referred: 0, pending: 0 },
  });
  const [patients, setPatients] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [search, setSearch] = useState("");
  const [inventoryForm, setInventoryForm] = useState({
    drug_name: "",
    amount: "",
    stock_quantity: "",
    reorder_level: "",
    expiry_date: "",
  });
  const [restockAmounts, setRestockAmounts] = useState({});
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [reportPeriod, setReportPeriod] = useState("1m");
  const hasInitializedSearchRef = useRef(false);
  const hasInitializedPeriodRef = useRef(false);

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
        fetchReportSummary(reportPeriod),
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
    [debouncedSearch, reportPeriod]
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

  useEffect(() => {
    if (!hasInitializedPeriodRef.current) {
      hasInitializedPeriodRef.current = true;
      return;
    }
    refresh({ source: "report-period" }).catch(() => {});
  }, [reportPeriod, refresh]);

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
    if (
      !inventoryForm.drug_name ||
      !inventoryForm.amount ||
      !inventoryForm.stock_quantity ||
      !inventoryForm.reorder_level ||
      !inventoryForm.expiry_date
    ) {
      setError("Fill all inventory fields.");
      return;
    }
    try {
      await createInventory({
        drug_name: inventoryForm.drug_name,
        amount: inventoryForm.amount,
        stock_quantity: Number(inventoryForm.stock_quantity),
        reorder_level: Number(inventoryForm.reorder_level),
        expiry_date: inventoryForm.expiry_date,
      });
      setInventoryForm({ drug_name: "", amount: "", stock_quantity: "", reorder_level: "", expiry_date: "" });
      setStatusMessage("Inventory item created.");
      await refresh({ source: "after-create-inventory" });
    } catch (actionError) {
      setError(actionError.message);
    }
  }, [inventoryForm, refresh]);

  const handleRestock = useCallback(async (id) => {
    const quantity = Number(restockAmounts[id]?.quantity);
    const expiryDate = restockAmounts[id]?.expiry_date;
    if (!quantity || quantity < 1 || !expiryDate) {
      setError("Enter a valid restock quantity and expiry date.");
      return;
    }
    try {
      await restockInventoryItem(id, { quantity, expiry_date: expiryDate });
      setRestockAmounts((prev) => ({ ...prev, [id]: { quantity: "", expiry_date: "" } }));
      setStatusMessage("Inventory restocked.");
      await refresh({ source: "after-restock" });
    } catch (actionError) {
      setError(actionError.message);
    }
  }, [refresh, restockAmounts]);

  const handleDownloadReport = useCallback(async () => {
    try {
      await downloadReport(reportPeriod);
    } catch (downloadError) {
      setError(downloadError.message);
    }
  }, [reportPeriod]);

  return (
    <div className="admin-page">
      <div className="admin-container">
        <Header currentUser={currentUser} onLogout={onLogout} onDownloadReport={handleDownloadReport} />
        {statusMessage && <p className="admin-status-success">{statusMessage}</p>}
        {error && <p className="admin-error">{error}</p>}
        {lastUpdated && <p className="admin-status-box">Last updated: {lastUpdated.toLocaleTimeString()}</p>}
        {loading && <p className="admin-status-box">Loading admin dashboard...</p>}
        <ReportControls reportPeriod={reportPeriod} setReportPeriod={setReportPeriod} />
        <p className="admin-status-box">Reporting period: {summary.period_label}</p>
        <SummaryCards summary={summary} />
        <OutcomePanel summary={summary.outcome_summary || {}} referralCases={summary.referral_cases} />
        <PendingUsersPanel users={pendingUsers} onApprove={handleApprove} onReject={handleReject} />
        <PatientsByCamp items={summary.patients_per_camp} />
        <DrugsByCamp items={summary.drugs_issued_per_camp} />
        <DrugUsagePanel items={summary.drug_usage_by_name || []} />
        <DiagnosisDistributionPanel items={summary.diagnosis_distribution_per_camp || []} />
        <CommonConditionsPanel items={summary.most_common_conditions || []} />
        <DrugTrendPanel items={summary.drug_usage_trends || []} />
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
