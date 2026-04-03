import subprocess
import sys
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
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
]


def main():
    overall_failed = 0
    for name in TEST_FILES:
        print(f"\n=== RUNNING {name} ===")
        completed = subprocess.run(
            [sys.executable, str(TEST_DIR / name)],
            cwd=str(TEST_DIR),
            text=True,
            capture_output=True,
        )
        if completed.stdout.strip():
            print(completed.stdout.strip())
        if completed.stderr.strip():
            print(completed.stderr.strip())
        file_result = "PASSED" if completed.returncode == 0 else "FAILED"
        print(f"=== RESULT {name}: {file_result} ===")
        if completed.returncode != 0:
            overall_failed += 1

    print(f"\nTOTAL FAILED FILES: {overall_failed}")
    print("PASSED" if overall_failed == 0 else "FAILED")
    return 0 if overall_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
