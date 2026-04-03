from test_helpers import CaseCollector, auth_token_for, create_patient, ensure_backend, fetch_queue, print_summary, submit_triage


def main():
    collector = CaseCollector("03 Triage Processing Tests")
    ok, message = ensure_backend()
    collector.check("backend_ping", ok, message)
    if not ok:
        return print_summary("03 Triage Processing Tests", collector)

    reg_token, _ = auth_token_for("registration", "triage_reg")
    nurse_token, _ = auth_token_for("nurse", "triage_nurse")
    collector.check("registration_login", reg_token is not None, "")
    collector.check("nurse_login", nurse_token is not None, "")
    if not reg_token or not nurse_token:
        return print_summary("03 Triage Processing Tests", collector)

    status, patient = create_patient(reg_token, camp="Camp Triage")
    patient_id = patient.get("id") if isinstance(patient, dict) else None
    collector.check("patient_created", status in (200, 201) and patient_id, f"status={status}")

    status, queue = fetch_queue(nurse_token)
    queue_ids = {item["id"] for item in queue} if isinstance(queue, list) else set()
    collector.check("patient_visible_in_triage_queue", status == 200 and patient_id in queue_ids, f"status={status}")

    status, data = submit_triage(nurse_token, patient_id, doctor_type="general_doctor")
    collector.check("submit_triage", status in (200, 201), f"status={status}")
    collector.check("triage_bmi_returned", isinstance(data, dict) and data.get("bmi") is not None, str(data))

    status, queue = fetch_queue(nurse_token)
    queue_ids = {item["id"] for item in queue} if isinstance(queue, list) else set()
    collector.check("patient_removed_from_triage_queue", status == 200 and patient_id not in queue_ids, f"status={status}")
    return print_summary("03 Triage Processing Tests", collector)


if __name__ == "__main__":
    raise SystemExit(main())
