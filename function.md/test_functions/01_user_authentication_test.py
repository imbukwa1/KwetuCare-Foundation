from test_helpers import CaseCollector, auth_token_for, ensure_backend, login_user, print_summary, run_load, signup_user


def main():
    collector = CaseCollector("01 User Authentication Tests")
    ok, message = ensure_backend()
    collector.check("backend_ping", ok, message)
    if not ok:
        return print_summary("01 User Authentication Tests", collector)

    status, _, email, password = signup_user("registration", "auth_reg")
    collector.check("signup_registration", status in (200, 201), f"status={status}")

    status, data = login_user(email, password)
    collector.check(
        "login_registration",
        status == 200 and isinstance(data, dict) and data.get("access") and data.get("refresh"),
        f"status={status}",
    )

    status, _ = login_user(email, "WrongPassword123!")
    collector.check("invalid_login_rejected", status == 400, f"status={status}")

    token, details = auth_token_for("admin", "auth_admin")
    collector.check("signup_and_login_admin", token is not None, str(details))

    def load_signup(index):
        status, _, _, _ = signup_user("nurse", f"auth_load_{index}")
        return status in (200, 201), f"status={status}"

    ok, info = run_load("concurrent_signup", load_signup)
    collector.check("concurrent_signup_load", ok, info)
    return print_summary("01 User Authentication Tests", collector)


if __name__ == "__main__":
    raise SystemExit(main())
