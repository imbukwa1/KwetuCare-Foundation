import json
import os
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib import error, request


PROJECT_ROOT = Path(r"C:\Users\imbuk\kwetucare-foundation")
BACKEND_ROOT = PROJECT_ROOT / "backend"
FRONTEND_ROOT = PROJECT_ROOT
API_BASE_URL = os.getenv("KCF_API_BASE_URL", "http://127.0.0.1:8000/api")
PING_URL = os.getenv("KCF_PING_URL", "http://127.0.0.1:8000/ping/")
DEFAULT_PASSWORD = os.getenv("KCF_TEST_PASSWORD", "Test12345!")
LOAD_USERS = int(os.getenv("KCF_LOAD_USERS", "20"))


def decode_body(raw):
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def api_request(method, path, payload=None, token=None, timeout=30):
    url = f"{API_BASE_URL}{path}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, data=data, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return response.status, decode_body(response.read())
    except error.HTTPError as exc:
        return exc.code, decode_body(exc.read())
    except Exception as exc:  # network/runtime failures
        return 0, str(exc)


def random_suffix():
    return uuid.uuid4().hex[:8]


def random_email(prefix):
    return f"{prefix}_{random_suffix()}@example.com"


def signup_user(role, prefix, *, full_name=None, password=DEFAULT_PASSWORD):
    email = random_email(prefix)
    payload = {
        "full_name": full_name or f"{prefix.title()} User {random_suffix()}",
        "email": email,
        "password": password,
        "role": role,
    }
    status, data = api_request("POST", "/auth/signup/", payload)
    return status, data, email, password


def login_user(identifier, password=DEFAULT_PASSWORD):
    payload = {"username": identifier, "password": password}
    return api_request("POST", "/auth/login/", payload)


def auth_token_for(role, prefix):
    status, data, email, password = signup_user(role, prefix)
    if status not in (200, 201):
        return None, f"signup failed: {status} {data}"
    status, data = login_user(email, password)
    if status != 200 or not isinstance(data, dict) or not data.get("access"):
        return None, f"login failed: {status} {data}"
    return data["access"], {"email": email, "password": password, "user": data.get("user", {})}


def create_patient(token, *, name=None, camp="Main Camp", location="Main Location", priority="normal"):
    payload = {
        "name": name or f"Patient {random_suffix()}",
        "age": 28,
        "gender": "female",
        "phone": f"07{uuid.uuid4().int % 100000000:08d}",
        "camp": camp,
        "location": location,
        "next_of_kin": "Test Kin",
        "priority": priority,
        "has_child": False,
    }
    return api_request("POST", "/patients/", payload, token=token)


def submit_triage(token, patient_id, *, doctor_type="general_doctor", requires_blood_sugar_check=False):
    payload = {
        "patient_id": patient_id,
        "blood_pressure": "120/80",
        "temperature": "36.8",
        "weight": "62.0",
        "height": "1.68",
        "heart_rate": 80,
        "respiratory_rate": 18,
        "spo2": 98,
        "nurse_notes": "Stable at triage",
        "requires_blood_sugar_check": requires_blood_sugar_check,
    }
    if not requires_blood_sugar_check:
        payload["assigned_doctor_type"] = doctor_type
    return api_request("POST", "/triage/", payload, token=token)


def submit_blood_sugar(token, patient_id, *, doctor_type="general_doctor"):
    payload = {
        "patient_id": patient_id,
        "blood_sugar_level": "6.2",
        "test_type": "random",
        "notes": "Within acceptable range",
        "assigned_doctor_type": doctor_type,
    }
    return api_request("POST", "/blood-sugar/", payload, token=token)


def create_inventory(token, *, drug_name="Paracetamol", amount="500mg", stock_quantity=20, reorder_level=5, expiry_date="2027-12-31"):
    payload = {
        "drug_name": drug_name,
        "amount": amount,
        "stock_quantity": stock_quantity,
        "reorder_level": reorder_level,
        "expiry_date": expiry_date,
    }
    return api_request("POST", "/inventory/", payload, token=token)


def submit_consultation(token, patient_id, *, diagnosis="General review", is_referral_case=False, drug_name="Paracetamol", amount="500mg"):
    payload = {
        "patient_id": patient_id,
        "diagnosis": diagnosis,
        "isReferralCase": is_referral_case,
        "doctorNotes": "Consultation notes",
        "recommendations": "Return if symptoms worsen",
        "followUpInstructions": "Review in one week",
        "prescriptions": [
            {
                "drug_name": drug_name,
                "dosage": amount,
                "quantity": 1,
                "frequency": "daily",
                "status": "pending",
            }
        ],
    }
    return api_request("POST", "/consultations/", payload, token=token)


def fetch_queue(token):
    return api_request("GET", "/queue/", token=token)


def fetch_patient_detail(token, patient_id):
    return api_request("GET", f"/patients/{patient_id}/", token=token)


def dispense_all_pending(token, patient_id):
    status, detail = fetch_patient_detail(token, patient_id)
    if status != 200 or not isinstance(detail, dict):
        return status, detail
    consultation = detail.get("consultation") or {}
    prescriptions = consultation.get("prescriptions") or detail.get("prescriptions") or []
    payload = {
        "patient_id": patient_id,
        "prescriptions": [{"id": item["id"], "status": "given"} for item in prescriptions],
    }
    return api_request("POST", "/pharmacy/dispense/", payload, token=token)


def run_load(label, fn, users=LOAD_USERS):
    results = []
    with ThreadPoolExecutor(max_workers=min(users, 20)) as executor:
        futures = [executor.submit(fn, index) for index in range(users)]
        for future in as_completed(futures):
            results.append(future.result())
    passed = sum(1 for ok, _ in results if ok)
    failed = len(results) - passed
    return passed == len(results), f"{label}: {passed}/{len(results)} passed, {failed} failed"


def ensure_backend():
    try:
        with request.urlopen(PING_URL, timeout=10) as response:
            if response.status == 200:
                return True, "Backend reachable"
            return False, f"Unexpected ping status {response.status}"
    except Exception as exc:
        return False, f"Backend not reachable: {exc}"


def run_command(command, cwd):
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        shell=False,
    )
    output = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part)
    return completed.returncode == 0, output


class CaseCollector:
    def __init__(self, title):
        self.title = title
        self.results = []

    def check(self, name, condition, details=""):
        self.results.append((name, bool(condition), details))

    def summarize(self):
        passed = sum(1 for _, ok, _ in self.results if ok)
        total = len(self.results)
        failed = total - passed
        lines = [f"{self.title}", f"Passed: {passed}", f"Failed: {failed}"]
        for name, ok, details in self.results:
            prefix = "PASSED" if ok else "FAILED"
            line = f"{prefix} | {name}"
            if details:
                line += f" | {details}"
            lines.append(line)
        lines.append("PASSED" if failed == 0 else "FAILED")
        return "\n".join(lines), failed == 0


def print_summary(title, collector):
    text, success = collector.summarize()
    print(text)
    return 0 if success else 1
