from test_helpers import (
    CaseCollector,
    auth_token_for,
    create_inventory,
    create_patient,
    dispense_all_pending,
    ensure_backend,
    fetch_queue,
    fetch_patient_detail,
    print_summary,
    submit_consultation,
    submit_triage,
)


def main():
    collector = CaseCollector("05 Pharmacy Dispensing Tests")
    ok, message = ensure_backend()
    collector.check("backend_ping", ok, message)
    if not ok:
        return print_summary("05 Pharmacy Dispensing Tests", collector)

    admin_token, _ = auth_token_for("admin", "pharm_admin")
    reg_token, _ = auth_token_for("registration", "pharm_reg")
    nurse_token, _ = auth_token_for("nurse", "pharm_nurse")
    doctor_token, _ = auth_token_for("general_doctor", "pharm_doc")
    pharmacist_token, _ = auth_token_for("pharmacist", "pharm_user")
    if not all([admin_token, reg_token, nurse_token, doctor_token, pharmacist_token]):
        collector.check("role_logins", False, "one or more role logins failed")
        return print_summary("05 Pharmacy Dispensing Tests", collector)
    collector.check("role_logins", True, "all required role accounts ready")

    status, _ = create_inventory(admin_token, drug_name="Amoxicillin", amount="500mg", stock_quantity=20)
    collector.check("inventory_seeded", status in (200, 201), f"status={status}")

    status, patient = create_patient(reg_token, camp="Camp Pharmacy")
    patient_id = patient.get("id") if isinstance(patient, dict) else None
    collector.check("patient_created", status in (200, 201) and patient_id, f"status={status}")

    submit_triage(nurse_token, patient_id, doctor_type="general_doctor")
    submit_consultation(doctor_token, patient_id, diagnosis="Bacterial infection", drug_name="Amoxicillin", amount="500mg")

    status, queue = fetch_queue(pharmacist_token)
    queue_ids = {item["id"] for item in queue} if isinstance(queue, list) else set()
    collector.check("patient_visible_in_pharmacy_queue", status == 200 and patient_id in queue_ids, f"status={status}")

    status, data = dispense_all_pending(pharmacist_token, patient_id)
    collector.check("dispense_all_pending", status == 200, f"status={status}")

    status, detail = fetch_patient_detail(pharmacist_token, patient_id)
    collector.check("patient_complete_after_dispense", status == 200 and detail.get("status") == "complete", str(detail))
    return print_summary("05 Pharmacy Dispensing Tests", collector)


if __name__ == "__main__":
    raise SystemExit(main())
