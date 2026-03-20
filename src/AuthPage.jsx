import { useState } from "react";
import logo from "./kcf logo.jpeg";
import "./AuthPage.css";
import { login, signup } from "./api";

function InputField({ label, type, value, onChange, placeholder, required, rightIcon, onRightIconClick }) {
  return (
    <div className="input-field">
      <label>
        {label}
        <div className="input-wrapper">
          <input
            type={type}
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            required={required}
          />
          {rightIcon && (
            <button type="button" className="icon-btn" onClick={onRightIconClick}>
              {rightIcon}
            </button>
          )}
        </div>
      </label>
    </div>
  );
}

function SignupModal({ isOpen, onClose, onSubmit }) {
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    role: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (key) => (e) => {
    setForm((prev) => ({ ...prev, [key]: e.target.value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.username || !form.email || !form.password || !form.role) {
      alert("Please fill all fields");
      return;
    }

    setIsSubmitting(true);
    setError("");

    signup(form)
      .then(() => {
        alert("Signup successful. Wait for admin approval before logging in.");
        onSubmit();
        setForm({ username: "", email: "", password: "", role: "" });
        setShowPassword(false);
      })
      .catch((signupError) => {
        setError(signupError.message);
      })
      .finally(() => setIsSubmitting(false));
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3>Create Account</h3>
        <p className="modal-subtitle">Enter your details to create an account</p>
        <form onSubmit={handleSubmit} className="modal-form">
          <InputField
            label="Username"
            type="text"
            value={form.username}
            onChange={handleChange("username")}
            placeholder="e.g. imbuk"
            required
          />
          <InputField
            label="Email"
            type="email"
            value={form.email}
            onChange={handleChange("email")}
            placeholder="you@example.com"
            required
          />
          <InputField
            label="Password"
            type={showPassword ? "text" : "password"}
            value={form.password}
            onChange={handleChange("password")}
            placeholder="Enter password"
            required
            rightIcon={showPassword ? "Hide" : "Show"}
            onRightIconClick={() => setShowPassword((prev) => !prev)}
          />

          <div className="input-field">
            <label>
              Role
              <select value={form.role} onChange={handleChange("role")} required>
                <option value="">Select role</option>
                <option value="registration">Registration Officer</option>
                <option value="nurse">Nurse</option>
                <option value="doctor">Doctor</option>
                <option value="pharmacist">Pharmacist</option>
                <option value="admin">Admin</option>
              </select>
            </label>
          </div>
          {error && <p className="modal-error">{error}</p>}

          <div className="modal-actions">
            <button type="button" className="btn-muted" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-maroon" disabled={isSubmitting}>
              {isSubmitting ? "Signing Up..." : "Sign Up"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function AuthPage({ onAuthenticated }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loginError, setLoginError] = useState("");

  const handleLoginChange = (key) => (e) => {
    setLoginForm((prev) => ({ ...prev, [key]: e.target.value }));
  };

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    if (!loginForm.username || !loginForm.password) {
      alert("Please fill all login fields");
      return;
    }
    setIsLoggingIn(true);
    setLoginError("");

    login(loginForm)
      .then((data) => {
        onAuthenticated(data.user);
      })
      .catch((error) => {
        setLoginError(error.message);
      })
      .finally(() => setIsLoggingIn(false));
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <img src={logo} alt="Kwetu Care logo" className="auth-logo" />
        <h1>Welcome Back</h1>
        <p className="auth-subtitle">Login to Kwetu Care</p>
        <form className="auth-form" onSubmit={handleLoginSubmit}>
          <InputField
            label="Username"
            type="text"
            value={loginForm.username}
            onChange={handleLoginChange("username")}
            placeholder="Enter username"
            required
          />
          <InputField
            label="Password"
            type={showLoginPassword ? "text" : "password"}
            value={loginForm.password}
            onChange={handleLoginChange("password")}
            placeholder="Enter password"
            required
            rightIcon={showLoginPassword ? "Hide" : "Show"}
            onRightIconClick={() => setShowLoginPassword((prev) => !prev)}
          />
          {loginError && <p className="modal-error">{loginError}</p>}
          <button className="btn-maroon" type="submit" disabled={isLoggingIn}>
            {isLoggingIn ? "Logging In..." : "Login"}
          </button>
        </form>
        <div className="auth-footer">
          <span>Don’t have an account?</span>
          <button className="btn-link" onClick={() => setIsModalOpen(true)}>
            Sign Up
          </button>
        </div>
      </div>

      <SignupModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onSubmit={() => setIsModalOpen(false)} />
    </div>
  );
}
