# Doctor Consultation and Prescription

## Description

This function allows a doctor to create a consultation and prescribe drugs for a patient in the `doctor` stage.

Core endpoint:

- `POST /consultations/`

## Expected Behavior

- only a `doctor` can submit consultation
- patient must currently be in `doctor`
- at least one prescription is required
- duplicate drug names in the same consultation are rejected
- drug must exist in inventory
- patient status changes to `pharmacy`

## Test Case 1: Valid Consultation

Input:

```json
{
  "patient_id": 1,
  "doctor_notes": "Treat for fever and pain",
  "prescriptions": [
    {
      "drug_name": "Paracetamol",
      "dosage": "500",
      "quantity": 2,
      "frequency": "twice daily",
      "status": "pending"
    }
  ]
}
```

Expected output:

- HTTP `201`
- consultation created
- status moves to `pharmacy`

Pass/Fail:

- `PASSED` if patient enters pharmacy queue
- `FAILED` otherwise

## Test Case 2: Drug Not in Inventory

Input:

- prescription drug not in inventory

Expected output:

- HTTP `400`
- drug availability validation error

Pass/Fail:

- `PASSED` if request is rejected
- `FAILED` if unavailable drug is accepted

## Test Case 3: Duplicate Drug Names

Expected output:

- HTTP `400`
- duplicate drug error

Pass/Fail:

- `PASSED` if duplicate drugs are blocked
- `FAILED` otherwise

## Python Test Script

```python
import requests

TOKEN = "PUT_DOCTOR_ACCESS_TOKEN_HERE"
URL = "http://127.0.0.1:8000/api/consultations/"

payload = {
    "patient_id": 1,
    "doctor_notes": "Treat for fever and pain",
    "prescriptions": [
        {
            "drug_name": "Paracetamol",
            "dosage": "500",
            "quantity": 2,
            "frequency": "twice daily",
            "status": "pending",
        }
    ],
}

response = requests.post(URL, json=payload, headers={"Authorization": f"Bearer {TOKEN}"})

if response.status_code == 201:
    print("PASSED")
else:
    print("FAILED")
    print(response.status_code, response.text)
```

## High-Load Script: 100 Concurrent Consultation Requests

```python
import aiohttp
import asyncio

URL = "http://127.0.0.1:8000/api/consultations/"
TOKEN = "PUT_DOCTOR_ACCESS_TOKEN_HERE"

async def submit_consultation(session, patient_id):
    payload = {
        "patient_id": patient_id,
        "doctor_notes": "Load test consultation",
        "prescriptions": [
            {
                "drug_name": "Paracetamol",
                "dosage": "500",
                "quantity": 1,
                "frequency": "once daily",
                "status": "pending",
            }
        ],
    }
    async with session.post(URL, json=payload) as response:
        return response.status, await response.text()

async def main():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        results = await asyncio.gather(*[submit_consultation(session, i) for i in range(1, 101)])

    server_errors = [item for item in results if item[0] >= 500]
    if not server_errors:
        print("PASSED")
    else:
        print("FAILED")
        print(server_errors[:5])

asyncio.run(main())
```
