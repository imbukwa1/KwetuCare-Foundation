import re

from test_helpers import CaseCollector, auth_token_for, create_patient, ensure_backend, print_summary, run_load


def main():
    collector = CaseCollector("02 Patient Registration Tests")
    ok, message = ensure_backend()
    collector.check("backend_ping", ok, message)
    if not ok:
        return print_summary("02 Patient Registration Tests", collector)

    token, details = auth_token_for("registration", "patient_reg")
    collector.check("registration_user_login", token is not None, str(details))
    if not token:
        return print_summary("02 Patient Registration Tests", collector)

    status, data = create_patient(token)
    reg_no = data.get("reg_no") if isinstance(data, dict) else None
    collector.check("create_patient", status in (200, 201), f"status={status}")
    collector.check("reg_no_format", bool(reg_no and re.fullmatch(r"KCF-\d{4}-\d{4}", reg_no)), str(reg_no))
    collector.check("status_triage", isinstance(data, dict) and data.get("status") == "triage", str(data))

    def load_registration(index):
        status, _ = create_patient(token, name=f"Load Patient {index}", location=f"Location {index}")
        return status in (200, 201), f"status={status}"

    ok, info = run_load("concurrent_registration", load_registration)
    collector.check("concurrent_patient_registration", ok, info)
    return print_summary("02 Patient Registration Tests", collector)


if __name__ == "__main__":
    raise SystemExit(main())
