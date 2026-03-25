# Triage Processing

## Description

This function allows a nurse to record triage data and move the patient from `triage` to `doctor`.

Core endpoint:

- `POST /triage/`

## Expected Behavior

- only a `nurse` can submit triage
- patient must currently be in `triage`
- triage cannot be repeated for the same patient
- valid vitals are required
- patient status changes to `doctor`

## Required Inputs

- `patient_id`
- `blood_pressure`
- `temperature`
- `weight`
- `heart_rate`
- optional `nurse_notes`

## Test Case 1: Valid Triage Submission

Expected output:

- HTTP `201`
- triage record created
- patient status becomes `doctor`

Pass/Fail:

- `PASSED` if status changes from `triage` to `doctor`
- `FAILED` otherwise

## Test Case 2: Invalid Blood Pressure

Input:

- `blood_pressure = "high"`

Expected output:

- HTTP `400`
- blood pressure validation message

Pass/Fail:

- `PASSED` if request is rejected
- `FAILED` if invalid format is accepted

## Test Case 3: Duplicate Triage

Input:

- same `patient_id` after triage already exists

Expected output:

- HTTP `400`
- duplicate triage error

Pass/Fail:

- `PASSED` if second triage attempt is rejected
- `FAILED` if duplicate triage is accepted

## Python Test Script

```python
import requests

TOKEN = "PUT_NURSE_ACCESS_TOKEN_HERE"
URL = "http://127.0.0.1:8000/api/triage/"

payload = {
    "patient_id": 1,
    "blood_pressure": "120/80",
    "temperature": 36.8,
    "weight": 64.0,
    "heart_rate": 82,
    "nurse_notes": "Stable at triage",
}

response = requests.post(URL, json=payload, headers={"Authorization": f"Bearer {TOKEN}"})

if response.status_code == 201:
    print("PASSED")
else:
    print("FAILED")
    print(response.status_code, response.text)
```

## High-Load Script: 100 Concurrent Triage Attempts

Purpose:

- validate locking, duplicate prevention, and stage protection

```python
import aiohttp
import asyncio

URL = "http://127.0.0.1:8000/api/triage/"
TOKEN = "PUT_NURSE_ACCESS_TOKEN_HERE"

async def submit_triage(session, patient_id):
    payload = {
        "patient_id": patient_id,
        "blood_pressure": "120/80",
        "temperature": 36.8,
        "weight": 60.0,
        "heart_rate": 80,
        "nurse_notes": "Load test",
    }
    async with session.post(URL, json=payload) as response:
        return response.status, await response.text()

async def main():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        results = await asyncio.gather(*[submit_triage(session, i) for i in range(1, 101)])

    server_errors = [item for item in results if item[0] >= 500]
    if not server_errors:
        print("PASSED")
    else:
        print("FAILED")
        print(server_errors[:5])

asyncio.run(main())
```
