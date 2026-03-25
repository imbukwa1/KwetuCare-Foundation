# User Authentication

## Description

This function handles:

- signup
- login
- current user session lookup
- admin approval or rejection of users

Core endpoints:

- `POST /auth/signup/`
- `POST /auth/login/`
- `POST /auth/refresh/`
- `GET /auth/me/`
- `GET /auth/pending-users/`
- `POST /auth/users/<id>/approve/`
- `DELETE /auth/users/<id>/reject/`

## Expected Behavior

- A user can sign up with `full_name`, `email`, `password`, and `role`.
- A valid login returns JWT tokens and user details.
- `GET /auth/me/` returns the authenticated user.
- Admin can approve or reject pending users.
- Invalid credentials must be rejected.

## Test Case 1: Signup

Input:

```json
{
  "full_name": "Test Registration User",
  "email": "test_registration_user@example.com",
  "password": "Test12345",
  "role": "registration"
}
```

Expected output:

- HTTP `201`
- created user returned
- no validation error

Pass/Fail:

- `PASSED` if status is `201`
- `FAILED` otherwise

`curl`:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/signup/ ^
  -H "Content-Type: application/json" ^
  -d "{\"full_name\":\"Test Registration User\",\"email\":\"test_registration_user@example.com\",\"password\":\"Test12345\",\"role\":\"registration\"}"
```

## Test Case 2: Login

Input:

```json
{
  "username": "test_registration_user@example.com",
  "password": "Test12345"
}
```

Expected output:

- HTTP `200`
- `access`
- `refresh`
- `user.role`

Pass/Fail:

- `PASSED` if both tokens are returned
- `FAILED` otherwise

Python script:

```python
import requests

payload = {
    "username": "test_registration_user@example.com",
    "password": "Test12345",
}

response = requests.post("http://127.0.0.1:8000/api/auth/login/", json=payload)
data = response.json()

if response.status_code == 200 and data.get("access") and data.get("refresh"):
    print("PASSED")
else:
    print("FAILED")
    print(response.status_code, data)
```

## Test Case 3: Invalid Login

Input:

- correct email
- wrong password

Expected output:

- HTTP `401`
- invalid credentials message

Pass/Fail:

- `PASSED` if login is denied
- `FAILED` if login succeeds

## Test Case 4: Fetch Current User

Input:

- valid access token

Expected output:

- HTTP `200`
- authenticated user returned

Pass/Fail:

- `PASSED` if returned user email matches the logged-in user
- `FAILED` otherwise

## Test Case 5: Admin Approves User

Input:

- admin access token
- pending user ID

Expected output:

- HTTP `200`
- approved user returned

Pass/Fail:

- `PASSED` if `is_approved` is `true`
- `FAILED` otherwise

## High-Load Script: 100 Concurrent Signups

Purpose:

- verify signup handles concurrent requests without crashing

Python async script:

```python
import aiohttp
import asyncio

URL = "http://127.0.0.1:8000/api/auth/signup/"

async def create_user(session, index):
    payload = {
        "full_name": f"Load User {index}",
        "email": f"load_user_{index}@example.com",
        "password": "Test12345",
        "role": "registration",
    }
    async with session.post(URL, json=payload) as response:
        try:
            data = await response.json()
        except Exception:
            data = await response.text()
        return response.status, data

async def main():
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[create_user(session, i) for i in range(1, 101)])

    passed = sum(1 for status, _ in results if status in {200, 201, 400})
    failed = [(status, data) for status, data in results if status not in {200, 201, 400}]

    if not failed:
        print("PASSED")
    else:
        print("FAILED")
        print(failed[:5])

asyncio.run(main())
```

Notes:

- `400` may be acceptable if the same email or validation conflict is intentionally triggered
- any `500` or crash is a failure
