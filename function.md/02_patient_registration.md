# Patient Registration

## Description

This function allows a registration officer to create a patient and send the patient to the `triage` stage.

Core endpoint:

- `POST /patients/`

## Expected Behavior

- only a `registration` user can register patients
- a registration number is auto-generated
- patient starts with status `triage`
- child details are required only if `has_child=true`

## Test Case 1: Register Adult Patient

Input:

```json
{
  "name": "Jane Doe",
  "age": 32,
  "gender": "Female",
  "phone": "+254700111222",
  "camp": "Nyandarwa",
  "village": "Village A",
  "next_of_kin": "John Doe",
  "has_child": false,
  "priority": "normal"
}
```

Expected output:

- HTTP `201`
- `reg_no` in format `KCF-YYYY-####`
- `status = triage`

Pass/Fail:

- `PASSED` if patient is created with generated `reg_no`
- `FAILED` otherwise

## Test Case 2: Register Child Case

Input:

```json
{
  "name": "Parent One",
  "age": 40,
  "gender": "Female",
  "phone": "+254700333444",
  "camp": "Rumuruti",
  "village": "Village B",
  "next_of_kin": "Guardian Two",
  "has_child": true,
  "child_name": "Child One",
  "child_age": 5,
  "child_date_of_birth": "2021-01-15",
  "guardian_name": "Parent One",
  "priority": "urgent"
}
```

Expected output:

- HTTP `201`
- child details saved
- `status = triage`

Pass/Fail:

- `PASSED` if child case is accepted
- `FAILED` if validation fails unexpectedly

## Test Case 3: Missing Child Details

Input:

- `has_child=true`
- omit `child_name` or `guardian_name`

Expected output:

- HTTP `400`
- child validation errors

Pass/Fail:

- `PASSED` if registration is blocked
- `FAILED` if incomplete child data is accepted

## Python Test Script

```python
import requests

TOKEN = "PUT_REGISTRATION_ACCESS_TOKEN_HERE"
URL = "http://127.0.0.1:8000/api/patients/"

payload = {
    "name": "Jane Doe",
    "age": 32,
    "gender": "Female",
    "phone": "+254700111222",
    "camp": "Nyandarwa",
    "village": "Village A",
    "next_of_kin": "John Doe",
    "has_child": False,
    "priority": "normal",
}

response = requests.post(URL, json=payload, headers={"Authorization": f"Bearer {TOKEN}"})
data = response.json()

if response.status_code == 201 and str(data.get("reg_no", "")).startswith("KCF-") and data.get("status") == "triage":
    print("PASSED")
else:
    print("FAILED")
    print(response.status_code, data)
```

## High-Load Script: 100 Concurrent Registrations

```python
import aiohttp
import asyncio

URL = "http://127.0.0.1:8000/api/patients/"
TOKEN = "PUT_REGISTRATION_ACCESS_TOKEN_HERE"

async def register_patient(session, index):
    payload = {
        "name": f"Patient {index}",
        "age": 20 + (index % 40),
        "gender": "Male" if index % 2 == 0 else "Female",
        "phone": f"+254700{index:06d}",
        "camp": "Load Camp",
        "village": f"Village {index}",
        "next_of_kin": f"Kin {index}",
        "has_child": False,
        "priority": "normal",
    }
    async with session.post(URL, json=payload, headers={"Authorization": f"Bearer {TOKEN}"}) as response:
        try:
            data = await response.json()
        except Exception:
            data = await response.text()
        return response.status, data

async def main():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        results = await asyncio.gather(*[register_patient(session, i) for i in range(1, 101)])

    failures = [item for item in results if item[0] != 201]
    if not failures:
        print("PASSED")
    else:
        print("FAILED")
        print(failures[:5])

asyncio.run(main())
```
