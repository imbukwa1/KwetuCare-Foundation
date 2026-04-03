from test_helpers import (
    CaseCollector,
    auth_token_for,
    create_patient,
    ensure_backend,
    fetch_queue,
    print_summary,
    submit_blood_sugar,
    submit_triage,
)


def main():
    collector = CaseCollector("09 Blood Sugar Department Tests")
    ok, message = ensure_backend()
    collector.check("backend_ping", ok, message)
    if not ok:
        return print_summary("09 Blood Sugar Department Tests", collector)

    reg_token, _ = auth_token_for("registration", "bs_reg")
    nurse_token, _ = auth_token_for("nurse", "bs_nurse")
    blood_token, _ = auth_token_for("blood_sugar", "bs_lab")
    doctor_token, _ = auth_token_for("nutritionist", "bs_nutritionist")
    if not all([reg_token, nurse_token, blood_token, doctor_token]):
        collector.check("role_logins", False, "required role login failed")
        return print_summary("09 Blood Sugar Department Tests", collector)
    collector.check("role_logins", True, "all required role accounts ready")

    status, patient = create_patient(reg_token, camp="Camp Sugar")
    patient_id = patient.get("id") if isinstance(patient, dict) else None
    collector.check("patient_created", status in (200, 201) and patient_id, f"status={status}")

    status, _ = submit_triage(nurse_token, patient_id, requires_blood_sugar_check=True)
    collector.check("triage_to_blood_sugar", status in (200, 201), f"status={status}")

    status, queue = fetch_queue(blood_token)
    queue_ids = {item["id"] for item in queue} if isinstance(queue, list) else set()
    collector.check("patient_visible_in_blood_sugar_queue", status == 200 and patient_id in queue_ids, f"status={status}")

    status, data = submit_blood_sugar(blood_token, patient_id, doctor_type="nutritionist")
    collector.check("blood_sugar_submission", status in (200, 201), f"status={status}")

    status, queue = fetch_queue(doctor_token)
    queue_ids = {item["id"] for item in queue} if isinstance(queue, list) else set()
    collector.check("patient_redirected_to_selected_specialist", status == 200 and patient_id in queue_ids, f"status={status}")
    return print_summary("09 Blood Sugar Department Tests", collector)


if __name__ == "__main__":
    raise SystemExit(main())
