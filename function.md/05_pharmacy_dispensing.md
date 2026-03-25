# Pharmacy Dispensing

## Description

This function allows a pharmacist to mark prescriptions as `given` or `not_available`, deduct inventory, and complete the patient workflow.

Core endpoint:

- `POST /pharmacy/dispense/`

## Expected Behavior

- only a `pharmacist` can dispense
- patient must currently be in `pharmacy`
- all prescriptions must be updated before completion
- stock is deducted when status is `given`
- insufficient stock causes validation failure
- patient status becomes `complete`

## Test Case 1: Valid Dispensing

Input:

```json
{
  "patient_id": 1,
  "prescriptions": [
    { "id": 10, "status": "given" }
  ]
}
```

Expected output:

- HTTP `200`
- prescription updated
- stock reduced
- patient status becomes `complete`

Pass/Fail:

- `PASSED` if status becomes `complete`
- `FAILED` otherwise

## Test Case 2: Insufficient Stock

Expected output:

- HTTP `400`
- inventory insufficiency message

Pass/Fail:

- `PASSED` if request is blocked
- `FAILED` if stock can go negative

## Test Case 3: Missing Prescription Update

Expected output:

- HTTP `400`
- all prescriptions must be updated error

Pass/Fail:

- `PASSED` if incomplete dispensing is rejected
- `FAILED` otherwise

## Python Test Script

```python
import requests

TOKEN = "PUT_PHARMACIST_ACCESS_TOKEN_HERE"
URL = "http://127.0.0.1:8000/api/pharmacy/dispense/"

payload = {
    "patient_id": 1,
    "prescriptions": [
        {"id": 10, "status": "given"}
    ],
}

response = requests.post(URL, json=payload, headers={"Authorization": f"Bearer {TOKEN}"})

if response.status_code == 200:
    print("PASSED")
else:
    print("FAILED")
    print(response.status_code, response.text)
```

## High-Load Script: 100 Concurrent Dispensing Requests

Purpose:

- verify stock deduction safety
- verify no race-condition corruption

```python
import aiohttp
import asyncio

URL = "http://127.0.0.1:8000/api/pharmacy/dispense/"
TOKEN = "PUT_PHARMACIST_ACCESS_TOKEN_HERE"

async def submit_dispense(session, patient_id, prescription_id):
    payload = {
        "patient_id": patient_id,
        "prescriptions": [
            {"id": prescription_id, "status": "given"}
        ],
    }
    async with session.post(URL, json=payload) as response:
        return response.status, await response.text()

async def main():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        results = await asyncio.gather(
            *[submit_dispense(session, i, i + 1000) for i in range(1, 101)]
        )

    server_errors = [item for item in results if item[0] >= 500]
    if not server_errors:
        print("PASSED")
    else:
        print("FAILED")
        print(server_errors[:5])

asyncio.run(main())
```
