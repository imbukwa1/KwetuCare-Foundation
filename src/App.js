import './App.css';
import { useEffect, useState } from 'react';
import AdminDashboardPage from './AdminDashboardPage';
import AuthPage from './AuthPage';
import DoctorConsultationPage from './DoctorConsultationPage';
import PatientIntakeForm from './PatientIntakeForm';
import PharmacyPage from './PharmacyPage';
import TriagePage from './TriagePage';
import { clearTokens, fetchCurrentUser, getStoredAccessToken } from './api';

function PendingApprovalView({ user, onLogout }) {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Account Pending Approval</h1>
        <p className="auth-subtitle">
          {user.username}, your account exists but an admin must approve it before you can use the system.
        </p>
        <button className="btn-maroon" onClick={onLogout}>
          Logout
        </button>
      </div>
    </div>
  );
}

function renderDashboard(user, onLogout) {
  switch (user.role) {
    case 'registration':
      return <PatientIntakeForm currentUser={user} onLogout={onLogout} />;
    case 'nurse':
      return <TriagePage currentUser={user} onLogout={onLogout} />;
    case 'doctor':
      return <DoctorConsultationPage currentUser={user} onLogout={onLogout} />;
    case 'pharmacist':
      return <PharmacyPage currentUser={user} onLogout={onLogout} />;
    case 'admin':
      return <AdminDashboardPage currentUser={user} onLogout={onLogout} />;
    default:
      return <PendingApprovalView user={user} onLogout={onLogout} />;
  }
}

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function restoreSession() {
      if (!getStoredAccessToken()) {
        setLoading(false);
        return;
      }

      try {
        const currentUser = await fetchCurrentUser();
        setUser(currentUser);
      } catch (error) {
        clearTokens();
      } finally {
        setLoading(false);
      }
    }

    restoreSession();
  }, []);

  const handleLogout = () => {
    clearTokens();
    setUser(null);
  };

  if (loading) {
    return <div className="auth-page"><div className="auth-card"><h1>Loading...</h1></div></div>;
  }

  if (!user) {
    return <AuthPage onAuthenticated={setUser} />;
  }

  if (!user.is_approved) {
    return <PendingApprovalView user={user} onLogout={handleLogout} />;
  }

  return renderDashboard(user, handleLogout);
}

export default App;
