import { useEffect, useState } from "react";
import logo from "./kcf logo.jpeg";
import "./AuthPage.css";
import { login, resendVerificationCode, signup, verifyEmail } from "./api";

const ROLE_OPTIONS = [
  { value: "registration", label: "Registration Officer" },
  { value: "nurse", label: "Nurse" },
  { value: "blood_sugar", label: "Blood Sugar Department" },
  { value: "general_doctor", label: "General Doctor" },
  { value: "pediatrician", label: "Pediatrician" },
  { value: "gynecologist", label: "Gynecologist" },
  { value: "obstetrician", label: "Obstetrician" },
  { value: "nutritionist", label: "Nutritionist" },
  { value: "dental", label: "Dentist" },
  { value: "optician", label: "Optician" },
  { value: "pharmacist", label: "Pharmacist" },
  { value: "admin", label: "Admin" },
];

function InputField({ label, type, value, onChange, placeholder, rightIcon, onRightIconClick, inputMode }) {
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
            inputMode={inputMode}
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
  const [verificationCode, setVerificationCode] = useState("");
  const [verificationEmail, setVerificationEmail] = useState("");
  const [step, setStep] = useState("signup");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (isOpen) {
      setForm(INITIAL_SIGNUP_FORM);
      setVerificationCode("");
      setVerificationEmail("");
      setStep("signup");
      setShowPassword(false);
      setIsSubmitting(false);
      setError("");
      setNotice("");
    }
  }, [isOpen]);

  const clearMessages = () => {
    setError("");
    setNotice("");
  };

  const handleChange = (key) => (e) => {
    clearMessages();
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

    if (!normalizedForm.full_name || !normalizedForm.email || !normalizedForm.password || !normalizedForm.role) {
      setError("Please fill in all fields.");
      return;
    }

    if (normalizedForm.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setIsSubmitting(true);
    clearMessages();

    signup(normalizedForm)
      .then((data) => {
        if (data.requires_email_verification) {
          setVerificationEmail(normalizedForm.email);
          setStep("verify");
          setNotice("We sent a 6-digit verification code to your email.");
        } else {
          alert("Signup successful. You can now log in with your email and password.");
          onSubmit();
        }
      })
      .catch((signupError) => {
        setError(signupError.message);
      })
      .finally(() => setIsSubmitting(false));
  };

  const handleVerifySubmit = (e) => {
    e.preventDefault();
    if (!verificationCode.trim()) {
      setError("Enter the 6-digit verification code.");
      return;
    }

    setIsSubmitting(true);
    clearMessages();
    verifyEmail({ email: verificationEmail, code: verificationCode.trim() })
      .then(() => {
        alert("Email verified. The admin has been notified and will review your account.");
        onSubmit();
      })
      .catch((verifyError) => {
        setError(verifyError.message);
      })
      .finally(() => setIsSubmitting(false));
  };

  const handleResendCode = () => {
    if (!verificationEmail) return;
    setIsSubmitting(true);
    clearMessages();
    resendVerificationCode({ email: verificationEmail })
      .then(() => {
        setVerificationCode("");
        setNotice("A new verification code has been sent.");
      })
      .catch((resendError) => {
        setError(resendError.message);
      })
      .finally(() => setIsSubmitting(false));
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3>Create Account</h3>
        <p className="modal-subtitle">
          {step === "signup" ? "Enter your details to create an account" : `Enter the code sent to ${verificationEmail}`}
        </p>

        {step === "signup" ? (
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
                      clearMessages();
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
            {notice && <p className="modal-success">{notice}</p>}
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
        ) : (
          <form onSubmit={handleVerifySubmit} className="modal-form" noValidate>
            <InputField
              label="Verification Code"
              type="text"
              value={verificationCode}
              onChange={(event) => {
                clearMessages();
                setVerificationCode(event.target.value.replace(/\D/g, "").slice(0, 6));
              }}
              placeholder="6-digit code"
              inputMode="numeric"
            />
            <p className="modal-subtitle">The code expires in 10 minutes. After 3 failed attempts, request a new code.</p>
            {notice && <p className="modal-success">{notice}</p>}
            {error && <p className="modal-error">{error}</p>}
            <div className="modal-actions">
              <button type="button" className="btn-muted" onClick={handleResendCode} disabled={isSubmitting}>
                Resend Code
              </button>
              <button type="button" className="btn-muted" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn-maroon" disabled={isSubmitting}>
                {isSubmitting ? "Verifying..." : "Verify Email"}
              </button>
            </div>
          </form>
        )}
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
          <span>Don't have an account?</span>
          <button className="btn-link" onClick={() => setIsModalOpen(true)}>
            Sign Up
          </button>
        </div>
      </div>

      <SignupModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onSubmit={() => setIsModalOpen(false)} />
    </div>
  );
}
