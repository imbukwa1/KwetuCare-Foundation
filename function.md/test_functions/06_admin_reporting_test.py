from test_helpers import CaseCollector, api_request, auth_token_for, ensure_backend, print_summary


def main():
    collector = CaseCollector("06 Admin Reporting Tests")
    ok, message = ensure_backend()
    collector.check("backend_ping", ok, message)
    if not ok:
        return print_summary("06 Admin Reporting Tests", collector)

    admin_token, _ = auth_token_for("admin", "report_admin")
    collector.check("admin_login", admin_token is not None, "")
    if not admin_token:
        return print_summary("06 Admin Reporting Tests", collector)

    for period in ("1m", "3m", "1y"):
        status, data = api_request("GET", f"/admin/reports/summary/?period={period}", token=admin_token)
        collector.check(
            f"summary_{period}",
            status == 200 and isinstance(data, dict) and data.get("period_key") == period,
            f"status={status}",
        )

    status, data = api_request("GET", "/admin/reports/export/?period=1m", token=admin_token)
    collector.check("export_endpoint", status == 200 and isinstance(data, str) and "Kwetu Care Report" in data, f"status={status}")
    return print_summary("06 Admin Reporting Tests", collector)


if __name__ == "__main__":
    raise SystemExit(main())
