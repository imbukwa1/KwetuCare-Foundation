import { useMemo, useState } from "react";
import "./PatientIntakeForm.css";
import { createPatient } from "./api";
import logo from "./kcf logo.jpeg";

const REQUIRED_FIELDS = ["name", "age", "gender", "phone", "camp", "village", "nextOfKin"];

export default function PatientIntakeForm({ currentUser, onLogout }) {
  const [form, setForm] = useState({
    name: "",
    age: "",
    gender: "",
    phone: "",
    camp: "",
    village: "",
    nextOfKin: "",
    hasChild: false,
    childName: "",
    childAge: "",
    childDateOfBirth: "",
    guardianName: "",
    priority: "normal",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleChange = (key) => (e) => {
    const value = e.target.value;
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const allRequiredFilled = useMemo(() => {
    const baseFieldsFilled = REQUIRED_FIELDS.every((k) => form[k].toString().trim() !== "");
    if (!form.hasChild) {
      return baseFieldsFilled;
    }

    return (
      baseFieldsFilled &&
      form.childName.trim() !== "" &&
      form.childAge.toString().trim() !== "" &&
      form.childDateOfBirth.trim() !== "" &&
      form.guardianName.trim() !== ""
    );
  }, [form]);

  const isValidForm = allRequiredFilled;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isValidForm) return;

    setIsSubmitting(true);
    setError("");
    setMessage("");

    createPatient({
      name: form.name,
      age: Number(form.age),
      gender: form.gender,
      phone: form.phone,
      camp: form.camp,
      village: form.village,
      next_of_kin: form.nextOfKin,
      has_child: form.hasChild,
      child_name: form.hasChild ? form.childName : "",
      child_age: form.hasChild ? Number(form.childAge) : null,
      child_date_of_birth: form.hasChild ? form.childDateOfBirth : null,
      guardian_name: form.hasChild ? form.guardianName : "",
      priority: form.priority,
    })
      .then((patient) => {
        setMessage(`Registration complete for ${patient.name}. Reg No: ${patient.reg_no}. Queued for triage.`);
        setForm({
          name: "",
          age: "",
          gender: "",
          phone: "",
          camp: "",
          village: "",
          nextOfKin: "",
          hasChild: false,
          childName: "",
          childAge: "",
          childDateOfBirth: "",
          guardianName: "",
          priority: "normal",
        });
      })
      .catch((submitError) => {
        setError(submitError.message);
      })
      .finally(() => setIsSubmitting(false));
  };

  return (
    <div className="kcf-page">
      <div className="kcf-card">
        <header className="kcf-header">
          <div className="kcf-header-top">
            <div className="kcf-logo">
              <img src={logo} alt="KCF logo" className="site-logo" />
            </div>
            <div className="kcf-header-meta">
              <span className="kcf-meta">Kwetu Care Facility (KCF) {currentUser ? `- ${currentUser.username}` : ""}</span>
            </div>
            {onLogout && (
              <button className="kcf-logout-button" type="button" onClick={onLogout}>
                Logout
              </button>
            )}
          </div>
          <h1>Patient Intake Form</h1>
        </header>

        <form className="kcf-form" onSubmit={handleSubmit} noValidate>
          <div className="kcf-row">
            <label>
              Name <span>*</span>
              <input value={form.name} onChange={handleChange("name")} type="text" placeholder="Full name" required />
            </label>
            <label>
              Age <span>*</span>
              <input value={form.age} onChange={handleChange("age")} type="number" min="0" placeholder="Age" required />
            </label>
          </div>

          <div className="kcf-row">
            <label>
              Gender <span>*</span>
              <select value={form.gender} onChange={handleChange("gender")} required>
                <option value="">Select Gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </label>
          </div>

          <div className="kcf-row">
            <label>
              Phone Number <span>*</span>
              <input value={form.phone} onChange={handleChange("phone")} type="tel" placeholder="e.g. +254700000000" required />
            </label>
            <label>
              Camp <span>*</span>
              <input value={form.camp} onChange={handleChange("camp")} type="text" placeholder="Camp name" required />
            </label>
          </div>

          <div className="kcf-row">
            <label>
              Village <span>*</span>
              <input value={form.village} onChange={handleChange("village")} type="text" placeholder="Village" required />
            </label>
            <label>
              Next of Kin <span>*</span>
              <input value={form.nextOfKin} onChange={handleChange("nextOfKin")} type="text" placeholder="Next of Kin" required />
            </label>
          </div>

          <div className="kcf-row-inline">
            <label className="kcf-checkbox">
              <input
                checked={form.hasChild}
                onChange={(event) => {
                  const checked = event.target.checked;
                  setForm((prev) => ({
                    ...prev,
                    hasChild: checked,
                    childName: checked ? prev.childName : "",
                    childAge: checked ? prev.childAge : "",
                    childDateOfBirth: checked ? prev.childDateOfBirth : "",
                    guardianName: checked ? prev.guardianName : "",
                  }));
                }}
                type="checkbox"
              />
              Child present
            </label>
          </div>

          {form.hasChild && (
            <div className="kcf-child-card">
              <h3>Child Details</h3>
              <div className="kcf-row">
                <label>
                  Child Name <span>*</span>
                  <input
                    value={form.childName}
                    onChange={handleChange("childName")}
                    type="text"
                    placeholder="Child full name"
                    required
                  />
                </label>
                <label>
                  Child Age <span>*</span>
                  <input
                    value={form.childAge}
                    onChange={handleChange("childAge")}
                    type="number"
                    min="0"
                    placeholder="Child age"
                    required
                  />
                </label>
              </div>
              <div className="kcf-row">
                <label>
                  Date of Birth <span>*</span>
                  <input
                    value={form.childDateOfBirth}
                    onChange={handleChange("childDateOfBirth")}
                    type="date"
                    required
                  />
                </label>
                <label>
                  Guardian Name <span>*</span>
                  <input
                    value={form.guardianName}
                    onChange={handleChange("guardianName")}
                    type="text"
                    placeholder="Guardian name"
                    required
                  />
                </label>
              </div>
            </div>
          )}

          <div className="kcf-row">
            <label>
              Priority
              <select value={form.priority} onChange={handleChange("priority")}>
                <option value="normal">Normal</option>
                <option value="urgent">Urgent</option>
              </select>
            </label>
          </div>

          <p className="modal-subtitle">Registration number will be generated automatically after saving.</p>

          {message && <p className="kcf-success">{message}</p>}
          {error && <p className="modal-error">{error}</p>}

          <button className="kcf-button" type="submit" disabled={!isValidForm || isSubmitting}>
            {isSubmitting ? "Submitting..." : "Complete Registration & Queue for Triage"}
          </button>
        </form>
      </div>
    </div>
  );
}
