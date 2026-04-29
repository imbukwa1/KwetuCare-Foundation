from test_helpers import (
    CaseCollector,
    api_request,
    auth_token_for,
    create_inventory,
    create_patient,
    ensure_backend,
    print_summary,
    submit_consultation,
    submit_triage,
)


def main():
    collector = CaseCollector("13 Referral Reporting Details Tests")
    ok, message = ensure_backend()
    collector.check("backend_ping", ok, message)
    if not ok:
        return print_summary("13 Referral Reporting Details Tests", collector)

    admin_token, _ = auth_token_for("admin", "referral_report_admin")
    reg_token, _ = auth_token_for("registration", "referral_report_registration")
    nurse_token, _ = auth_token_for("nurse", "referral_report_nurse")
    doctor_token, _ = auth_token_for("general_doctor", "referral_report_doctor")
    collector.check(
        "role_logins",
        all([admin_token, reg_token, nurse_token, doctor_token]),
        "admin, registration, nurse, doctor ready",
    )
    if not all([admin_token, reg_token, nurse_token, doctor_token]):
        return print_summary("13 Referral Reporting Details Tests", collector)

    status, data = create_inventory(
        admin_token,
        drug_name="ReferralDrug",
        amount="250mg",
        stock_quantity=10,
        reorder_level=2,
        expiry_date="2027-12-31",
    )
    collector.check("inventory_seeded", status in (200, 201), f"status={status}")

    status, data = create_patient(reg_token, name="Referral Patient", camp="Camp Mandwla", location="Zone A")
    patient_id = data.get("id") if isinstance(data, dict) else None
    collector.check("patient_created", status in (200, 201) and patient_id, f"status={status}")
    if not patient_id:
        return print_summary("13 Referral Reporting Details Tests", collector)

    status, data = submit_triage(nurse_token, patient_id, doctor_type="general_doctor")
    collector.check("triage_submitted", status in (200, 201), f"status={status}")

    status, data = submit_consultation(
        doctor_token,
        patient_id,
        diagnosis="Referral Diagnosis",
        is_referral_case=True,
        drug_name="ReferralDrug",
        amount="250mg",
    )
    collector.check("consultation_submitted", status in (200, 201), f"status={status}")

    status, data = api_request("GET", "/admin/reports/summary/?period=1m", token=admin_token)
    referral_items = data.get("referral_case_details", []) if isinstance(data, dict) else []
    referral_entry = next((item for item in referral_items if item.get("patient_name") == "Referral Patient"), None)
    collector.check("summary_loaded", status == 200 and isinstance(data, dict), f"status={status}")
    collector.check(
        "referral_details_present",
        bool(referral_entry and referral_entry.get("diagnosis") == "Referral Diagnosis"),
        str(referral_entry),
    )
    collector.check(
        "referral_prescription_present",
        bool(referral_entry and any("ReferralDrug" in item for item in (referral_entry.get("prescriptions") or []))),
        str(referral_entry),
    )
    return print_summary("13 Referral Reporting Details Tests", collector)


if __name__ == "__main__":
    raise SystemExit(main())
