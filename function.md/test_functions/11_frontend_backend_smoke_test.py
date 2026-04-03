from test_helpers import BACKEND_ROOT, FRONTEND_ROOT, CaseCollector, ensure_backend, print_summary, run_command


def main():
    collector = CaseCollector("11 Frontend and Backend Smoke Tests")

    ok, message = ensure_backend()
    collector.check("backend_ping", ok, message)

    ok, output = run_command(["python", "manage.py", "check"], BACKEND_ROOT)
    collector.check("django_check", ok, output.splitlines()[-1] if output else "")

    ok, output = run_command(["npm.cmd", "run", "build"], FRONTEND_ROOT)
    collector.check("react_build", ok, output.splitlines()[-1] if output else "")
    return print_summary("11 Frontend and Backend Smoke Tests", collector)


if __name__ == "__main__":
    raise SystemExit(main())
