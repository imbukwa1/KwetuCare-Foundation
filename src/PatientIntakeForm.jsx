import { useMemo, useState } from "react";
import "./PatientIntakeForm.css";
import { createPatient } from "./api";

export default function PatientIntakeForm({ currentUser, onLogout }) {
  const [form, setForm] = useState({
    name: "",
    age: "",
    gender: "",
    phone: "",
    camp: "",
    village: "",
    nextOfKin: "",
    regNo: "",
    priority: "normal",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleChange = (key) => (e) => {
    const value = e.target.value;
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const required = ["name", "age", "gender", "phone", "camp", "village", "nextOfKin", "regNo"];

  const allRequiredFilled = useMemo(() => {
    return required.every((k) => form[k].toString().trim() !== "");
  }, [form, required]);

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
      reg_no: form.regNo,
      priority: form.priority,
    })
      .then((patient) => {
        setMessage(`Registration complete for ${patient.name}. Queued for triage.`);
        setForm({
          name: "",
          age: "",
          gender: "",
          phone: "",
          camp: "",
          village: "",
          nextOfKin: "",
          regNo: "",
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
          <div className="kcf-meta-like">
            <span className="kcf-meta">Kwetu Care Facility (KCF) {currentUser ? `- ${currentUser.username}` : ""}</span>
            <span className="kcf-reg">Reg No: {form.regNo || "____"}</span>
          </div>
          <h1>Patient Intake Form</h1>
          {onLogout && (
            <button className="kcf-button" type="button" onClick={onLogout}>
              Logout
            </button>
          )}
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

          <div className="kcf-row">
            <label>
              Registration Number <span>*</span>
              <input value={form.regNo} onChange={handleChange("regNo")} type="text" placeholder="e.g. KCF-001" required />
            </label>
            <label>
              Priority
              <select value={form.priority} onChange={handleChange("priority")}>
                <option value="normal">Normal</option>
                <option value="urgent">Urgent</option>
              </select>
            </label>
          </div>

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
