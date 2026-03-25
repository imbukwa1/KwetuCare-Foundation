import './App.css';
import { useEffect, useState } from 'react';
import AdminDashboardPage from './AdminDashboardPage';
import AuthPage from './AuthPage';
import DoctorConsultationPage from './DoctorConsultationPage';
import PatientIntakeForm from './PatientIntakeForm';
import PharmacyPage from './PharmacyPage';
import TriagePage from './TriagePage';
import { clearTokens, fetchCurrentUser, getStoredAccessToken } from './api';

const ROLE_PATHS = {
  registration: '/registration',
  nurse: '/triage',
  doctor: '/doctor',
  pharmacist: '/pharmacy',
  admin: '/admin',
};

function navigateTo(path, { replace = false } = {}) {
  if (window.location.pathname === path) {
    return;
  }

  const method = replace ? 'replaceState' : 'pushState';
  window.history[method]({}, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}

function getDefaultPathForUser(user) {
  if (!user?.is_approved) {
    return '/pending-approval';
  }

  return ROLE_PATHS[user.role] || '/';
}

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
  const [currentPath, setCurrentPath] = useState(window.location.pathname || '/');

  useEffect(() => {
    const handleLocationChange = () => setCurrentPath(window.location.pathname || '/');
    window.addEventListener('popstate', handleLocationChange);
    return () => window.removeEventListener('popstate', handleLocationChange);
  }, []);

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

  useEffect(() => {
    if (loading || !user) {
      return;
    }

    const expectedPath = getDefaultPathForUser(user);
    if (currentPath !== expectedPath) {
      navigateTo(expectedPath, { replace: true });
    }
  }, [currentPath, loading, user]);

  const handleLogout = () => {
    clearTokens();
    setUser(null);
    navigateTo('/', { replace: true });
  };

  if (loading) {
    return <div className="auth-page"><div className="auth-card"><h1>Loading...</h1></div></div>;
  }

  if (!user) {
    return <AuthPage onAuthenticated={(nextUser) => {
      setUser(nextUser);
      navigateTo(getDefaultPathForUser(nextUser), { replace: true });
    }} />;
  }

  if (!user.is_approved) {
    return <PendingApprovalView user={user} onLogout={handleLogout} />;
  }

  return renderDashboard(user, handleLogout);
}

export default App;
