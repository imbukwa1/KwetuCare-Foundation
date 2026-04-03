from test_helpers import CaseCollector, auth_token_for, create_inventory, create_patient, ensure_backend, fetch_queue, print_summary, submit_triage


def main():
    collector = CaseCollector("10 Specialist Workflow Tests")
    ok, message = ensure_backend()
    collector.check("backend_ping", ok, message)
    if not ok:
        return print_summary("10 Specialist Workflow Tests", collector)

    reg_token, _ = auth_token_for("registration", "spec_reg")
    nurse_token, _ = auth_token_for("nurse", "spec_nurse")
    pediatric_token, _ = auth_token_for("pediatrician", "spec_peds")
    general_token, _ = auth_token_for("general_doctor", "spec_gen")
    admin_token, _ = auth_token_for("admin", "spec_admin")
    if not all([reg_token, nurse_token, pediatric_token, general_token, admin_token]):
        collector.check("role_logins", False, "required role login failed")
        return print_summary("10 Specialist Workflow Tests", collector)
    collector.check("role_logins", True, "all specialist test accounts ready")

    create_inventory(admin_token, drug_name="Paracetamol", amount="500mg", stock_quantity=10)
    status, patient = create_patient(reg_token, camp="Camp Pediatric")
    patient_id = patient.get("id") if isinstance(patient, dict) else None
    collector.check("patient_created", status in (200, 201) and patient_id, f"status={status}")

    status, _ = submit_triage(nurse_token, patient_id, doctor_type="pediatrician")
    collector.check("triage_to_pediatrician", status in (200, 201), f"status={status}")

    status, pediatric_queue = fetch_queue(pediatric_token)
    pediatric_ids = {item["id"] for item in pediatric_queue} if isinstance(pediatric_queue, list) else set()
    collector.check("patient_visible_to_pediatrician", status == 200 and patient_id in pediatric_ids, f"status={status}")

    status, general_queue = fetch_queue(general_token)
    general_ids = {item["id"] for item in general_queue} if isinstance(general_queue, list) else set()
    collector.check("patient_hidden_from_general_doctor", status == 200 and patient_id not in general_ids, f"status={status}")
    return print_summary("10 Specialist Workflow Tests", collector)


if __name__ == "__main__":
    raise SystemExit(main())
