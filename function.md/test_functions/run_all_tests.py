import os
import subprocess
import sys
import time
from pathlib import Path
from urllib import error, request


TEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
TEST_DB_PATH = PROJECT_ROOT / "frontend" / "src" / ".kcf_test_data" / "test_db.sqlite3"
TEST_HOST = os.getenv("KCF_TEST_HOST", "127.0.0.1")
TEST_PORT = int(os.getenv("KCF_TEST_PORT", "8010"))
TEST_API_BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}/api"
TEST_PING_URL = f"http://{TEST_HOST}:{TEST_PORT}/ping/"
TEST_FILES = [
    "01_user_authentication_test.py",
    "02_patient_registration_test.py",
    "03_triage_processing_test.py",
    "04_doctor_consultation_and_prescription_test.py",
    "05_pharmacy_dispensing_test.py",
    "06_admin_reporting_test.py",
    "07_inventory_management_test.py",
    "08_realtime_sync_test.py",
    "09_blood_sugar_department_test.py",
    "10_specialist_workflows_test.py",
    "11_frontend_backend_smoke_test.py",
    "12_inventory_categories_and_visibility_test.py",
    "13_referral_reporting_details_test.py",
]


def wait_for_backend(url, timeout=45):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return True
        except error.URLError:
            pass
        except Exception:
            pass
        time.sleep(1)
    return False


def build_test_env():
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "backend_config.test_settings"
    env["KCF_API_BASE_URL"] = TEST_API_BASE_URL
    env["KCF_PING_URL"] = TEST_PING_URL
    return env


def prepare_test_database(env):
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    migrate = subprocess.run(
        [sys.executable, "manage.py", "migrate", "--noinput"],
        cwd=str(BACKEND_DIR),
        text=True,
        capture_output=True,
        env=env,
    )
    output = "\n".join(part for part in [migrate.stdout.strip(), migrate.stderr.strip()] if part)
    if migrate.returncode != 0:
        raise RuntimeError(output or "Failed to migrate test database.")


def start_test_backend(env):
    backend = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"{TEST_HOST}:{TEST_PORT}", "--noreload"],
        cwd=str(BACKEND_DIR),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    if not wait_for_backend(TEST_PING_URL):
        stdout, stderr = backend.communicate(timeout=5)
        raise RuntimeError(
            "Test backend did not start.\n"
            + "\n".join(part for part in [stdout.strip(), stderr.strip()] if part)
        )
    return backend


def stop_test_backend(process):
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main():
    env = build_test_env()
    print(f"Preparing isolated test database at {TEST_DB_PATH}")
    prepare_test_database(env)
    print(f"Starting isolated test backend on {TEST_PING_URL}")
    backend_process = start_test_backend(env)
    overall_failed = 0
    try:
        for name in TEST_FILES:
            print(f"\n=== RUNNING {name} ===")
            completed = subprocess.run(
                [sys.executable, str(TEST_DIR / name)],
                cwd=str(TEST_DIR),
                text=True,
                capture_output=True,
                env=env,
            )
            if completed.stdout.strip():
                print(completed.stdout.strip())
            if completed.stderr.strip():
                print(completed.stderr.strip())
            file_result = "PASSED" if completed.returncode == 0 else "FAILED"
            print(f"=== RESULT {name}: {file_result} ===")
            if completed.returncode != 0:
                overall_failed += 1
    finally:
        stop_test_backend(backend_process)

    print(f"\nTOTAL FAILED FILES: {overall_failed}")
    print("PASSED" if overall_failed == 0 else "FAILED")
    return 0 if overall_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
