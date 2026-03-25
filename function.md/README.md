# Kwetu Care Test Functions

This folder contains modular testing documents for the core functions of the Kwetu Care system.

Files:

- `01_user_authentication.md`
- `02_patient_registration.md`
- `03_triage_processing.md`
- `04_doctor_consultation_and_prescription.md`
- `05_pharmacy_dispensing.md`
- `06_admin_reporting.md`

Base backend URL:

```text
http://127.0.0.1:8000/api
```

Suggested local roles:

- `registration`
- `nurse`
- `doctor`
- `pharmacist`
- `admin`

General testing rules:

1. Run the backend before testing.
2. Use fresh test data where possible.
3. Record actual response status and response body.
4. Mark each test as:
   - `PASSED`
   - `FAILED`

Shared pass/fail rule:

- `PASSED` means the endpoint, role rule, workflow behavior, and returned data match the expected result.
- `FAILED` means the response code, returned data, validation, or workflow state does not match the expectation.

Shared backend startup:

```powershell
cd c:\Users\imbuk\kwetucare-foundation\backend
$env:POSTGRES_DB="kwetu_care"
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASSWORD="April2804#"
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="5432"
python -m uvicorn backend_config.asgi:application --host 127.0.0.1 --port 8000
```

Shared Python setup for scripts:

```powershell
pip install requests aiohttp
```

Notes:

- High-load examples target up to `100` concurrent users.
- Use a non-production database for concurrency and load testing.
- Some tests depend on previous stages being completed first.
