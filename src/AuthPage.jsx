import { useEffect, useState } from "react";
import logo from "./kcf logo.jpeg";
import "./AuthPage.css";
import { login, signup } from "./api";

const ROLE_OPTIONS = [
  { value: "registration", label: "Registration Officer" },
  { value: "nurse", label: "Nurse" },
  { value: "doctor", label: "Doctor" },
  { value: "pharmacist", label: "Pharmacist" },
  { value: "admin", label: "Admin" },
];

function InputField({ label, type, value, onChange, placeholder, rightIcon, onRightIconClick }) {
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

const INITIAL_SIGNUP_FORM = {
  full_name: "",
  email: "",
  password: "",
  role: "registration",
};

function SignupModal({ isOpen, onClose, onSubmit }) {
  const [form, setForm] = useState(INITIAL_SIGNUP_FORM);
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isOpen) {
      setForm(INITIAL_SIGNUP_FORM);
      setShowPassword(false);
      setIsSubmitting(false);
      setError("");
    }
  }, [isOpen]);

  const handleChange = (key) => (e) => {
    setError("");
    setForm((prev) => ({ ...prev, [key]: e.target.value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const normalizedForm = {
      full_name: form.full_name.trim(),
      email: form.email.trim(),
      password: form.password,
      role: form.role || "registration",
    };

    if (
      !normalizedForm.full_name ||
      !normalizedForm.email ||
      !normalizedForm.password ||
      !normalizedForm.role
    ) {
      setError("Please fill in all fields.");
      return;
    }

    if (normalizedForm.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setIsSubmitting(true);
    setError("");

    signup(normalizedForm)
      .then(() => {
        alert("Signup successful. Wait for admin approval before logging in with your email and password.");
        onSubmit();
        setForm(INITIAL_SIGNUP_FORM);
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
        <form onSubmit={handleSubmit} className="modal-form" noValidate>
          <InputField
            label="Full Name"
            type="text"
            value={form.full_name}
            onChange={handleChange("full_name")}
            placeholder="e.g. Aisha Mohamed"
          />
          <InputField
            label="Email"
            type="email"
            value={form.email}
            onChange={handleChange("email")}
            placeholder="you@example.com"
          />
          <InputField
            label="Password"
            type={showPassword ? "text" : "password"}
            value={form.password}
            onChange={handleChange("password")}
            placeholder="Minimum 8 characters"
            rightIcon={showPassword ? "Hide" : "Show"}
            onRightIconClick={() => setShowPassword((prev) => !prev)}
          />
          <p className="modal-subtitle">Password must be at least 8 characters.</p>

          <div className="input-field">
            <label>Role</label>
            <div className="role-grid">
              {ROLE_OPTIONS.map((roleOption) => (
                <button
                  key={roleOption.value}
                  type="button"
                  className={`role-chip ${form.role === roleOption.value ? "role-chip-active" : ""}`}
                  onClick={() => {
                    setError("");
                    setForm((prev) => ({ ...prev, role: roleOption.value }));
                  }}
                >
                  {roleOption.label}
                </button>
              ))}
            </div>
            <p className="role-selected">
              Selected role: {ROLE_OPTIONS.find((roleOption) => roleOption.value === form.role)?.label}
            </p>
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
            label="Email or Username"
            type="text"
            value={loginForm.username}
            onChange={handleLoginChange("username")}
            placeholder="Enter email or username"
          />
          <InputField
            label="Password"
            type={showLoginPassword ? "text" : "password"}
            value={loginForm.password}
            onChange={handleLoginChange("password")}
            placeholder="Enter password"
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
