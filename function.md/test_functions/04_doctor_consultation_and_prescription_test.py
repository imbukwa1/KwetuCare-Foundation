from test_helpers import (
    CaseCollector,
    auth_token_for,
    create_inventory,
    create_patient,
    ensure_backend,
    fetch_queue,
    print_summary,
    submit_consultation,
    submit_triage,
)


def main():
    collector = CaseCollector("04 Doctor Consultation and Prescription Tests")
    ok, message = ensure_backend()
    collector.check("backend_ping", ok, message)
    if not ok:
        return print_summary("04 Doctor Consultation and Prescription Tests", collector)

    admin_token, _ = auth_token_for("admin", "doc_admin")
    reg_token, _ = auth_token_for("registration", "doc_reg")
    nurse_token, _ = auth_token_for("nurse", "doc_nurse")
    doctor_token, _ = auth_token_for("general_doctor", "doc_general")
    collector.check("admin_login", admin_token is not None, "")
    collector.check("doctor_login", doctor_token is not None, "")
    if not all([admin_token, reg_token, nurse_token, doctor_token]):
        return print_summary("04 Doctor Consultation and Prescription Tests", collector)

    status, _ = create_inventory(admin_token, drug_name="Paracetamol", amount="500mg", stock_quantity=12)
    collector.check("inventory_seeded", status in (200, 201), f"status={status}")

    status, patient = create_patient(reg_token, camp="Camp Doctor")
    patient_id = patient.get("id") if isinstance(patient, dict) else None
    collector.check("patient_created", status in (200, 201) and patient_id, f"status={status}")

    status, _ = submit_triage(nurse_token, patient_id, doctor_type="general_doctor")
    collector.check("triage_completed", status in (200, 201), f"status={status}")

    status, queue = fetch_queue(doctor_token)
    queue_ids = {item["id"] for item in queue} if isinstance(queue, list) else set()
    collector.check("patient_visible_in_doctor_queue", status == 200 and patient_id in queue_ids, f"status={status}")

    status, data = submit_consultation(doctor_token, patient_id, diagnosis="Malaria review", is_referral_case=True)
    collector.check("consultation_submitted", status in (200, 201), f"status={status}")
    collector.check("consultation_to_pharmacy", isinstance(data, dict) and data.get("patient", {}).get("status", "pharmacy") == "pharmacy", str(data))
    return print_summary("04 Doctor Consultation and Prescription Tests", collector)


if __name__ == "__main__":
    raise SystemExit(main())
