# Admin Reporting

## Description

This function gives the admin visibility into:

- patients per camp
- drugs issued per camp
- specific drugs given per camp
- patients waiting per stage
- completed patient totals
- report export

Core endpoints:

- `GET /admin/reports/summary/`
- `GET /admin/reports/export/`
- `GET /admin/patients/`
- `GET /inventory/`

## Expected Behavior

- only an admin can access admin reporting endpoints
- summary data must return correctly structured counts
- export must download successfully
- patient list search must filter data

## Test Case 1: Summary Report

Expected output:

- HTTP `200`
- includes:
  - `patients_per_camp`
  - `drugs_issued_per_camp`
  - `drug_details_per_camp`
  - `stage_waiting_counts`
  - `completed_patients`

Pass/Fail:

- `PASSED` if all keys are present
- `FAILED` otherwise

## Test Case 2: Export Report

Expected output:

- HTTP `200`
- downloadable `.doc` content

Pass/Fail:

- `PASSED` if response content type is a document and not an error page
- `FAILED` otherwise

## Test Case 3: Search Patients

Input:

- `?search=KCF-2026-0001`

Expected output:

- matching patient rows only

Pass/Fail:

- `PASSED` if filtered results are correct
- `FAILED` otherwise

## Python Test Script

```python
import requests

TOKEN = "PUT_ADMIN_ACCESS_TOKEN_HERE"
URL = "http://127.0.0.1:8000/api/admin/reports/summary/"

response = requests.get(URL, headers={"Authorization": f"Bearer {TOKEN}"})
data = response.json()

required_keys = {
    "patients_per_camp",
    "drugs_issued_per_camp",
    "drug_details_per_camp",
    "stage_waiting_counts",
    "completed_patients",
}

if response.status_code == 200 and required_keys.issubset(data.keys()):
    print("PASSED")
else:
    print("FAILED")
    print(response.status_code, data)
```

## Load Test Script: 100 Concurrent Admin Summary Requests

Purpose:

- verify reporting endpoint remains responsive under read-heavy load

```python
import aiohttp
import asyncio

URL = "http://127.0.0.1:8000/api/admin/reports/summary/"
TOKEN = "PUT_ADMIN_ACCESS_TOKEN_HERE"

async def fetch_report(session):
    async with session.get(URL) as response:
        return response.status, await response.text()

async def main():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        results = await asyncio.gather(*[fetch_report(session) for _ in range(100)])

    failures = [item for item in results if item[0] != 200]
    if not failures:
        print("PASSED")
    else:
        print("FAILED")
        print(failures[:5])

asyncio.run(main())
```

## Manual Verification Checklist

1. Open admin dashboard.
2. Confirm patient counts per stage update correctly.
3. Confirm inventory and camp summaries render.
4. Download the report.
5. Confirm the report includes:
   - camp totals
   - specific drugs given per camp
   - quantity
   - amount

If all checks pass, print:

```text
PASSED
```

Otherwise print:

```text
FAILED
```
