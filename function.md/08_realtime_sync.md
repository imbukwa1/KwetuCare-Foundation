# 08. Realtime Sync

## Function Description
This function keeps user pages synchronized across roles using a hybrid approach:
- polling
- refresh-after-action
- WebSocket updates

It supports the Registration, Triage, Doctor, Pharmacy, and Admin flows by reducing stale data and improving multi-user visibility.

## Core Scope
- Poll data every few seconds while the tab is active
- Refresh immediately after successful data-changing actions
- Receive WebSocket events and refresh only when relevant
- Reconnect WebSocket after temporary disconnects
- Back off polling interval after repeated failures

## Frontend Files Involved
- `src/useHybridDataSync.js`
- `src/TriagePage.jsx`
- `src/DoctorConsultationPage.jsx`
- `src/PharmacyPage.jsx`
- `src/AdminDashboardPage.jsx`

## Backend Files Involved
- `backend/core/realtime.py`
- `backend/backend_config/asgi.py`
- `backend/backend_config/settings.py`
- `backend/core/serializers.py`

## WebSocket Runtime Requirement
WebSocket broadcasting requires the backend to run with ASGI.

### Example Command
```powershell
cd c:\Users\imbuk\kwetucare-foundation\backend
$env:POSTGRES_DB="kwetu_care"
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASSWORD="April2804#"
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="5432"
python -m uvicorn backend_config.asgi:application --host 127.0.0.1 --port 8000
```

## Broadcast Event Types
- `patient_created`
- `triage_completed`
- `consultation_completed`
- `prescription_updated`
- `drug_dispensed`
- `inventory_created`
- `inventory_restocked`
- `user_approved`
- `user_rejected`

## Expected Behavior
- Triage page refreshes when a new patient enters `triage`
- Doctor page refreshes when a patient enters `doctor`
- Pharmacy page refreshes when a patient enters `pharmacy`
- Admin page refreshes when workflow or inventory changes occur
- Polling runs only while the browser tab is active
- Polling interval increases after repeated failures
- Successful fetch resets polling interval back to normal
- WebSocket reconnects after disconnects without creating duplicate sockets

## Test Case 1: Polling Refresh

### Input
- Open Triage page
- Create a new patient from Registration

### Expected Output
- Triage queue updates within `3–5` seconds even if no manual refresh happens

### Pass/Fail Condition
- `PASSED` if the patient appears automatically
- `FAILED` if a manual page refresh is required

## Test Case 2: Refresh After Action

### Input
- Submit triage for a patient

### Expected Output
- Patient disappears immediately from the current nurse queue
- Doctor queue updates immediately for the acting user

### Pass/Fail Condition
- `PASSED` if UI updates instantly after action success
- `FAILED` if UI remains stale until polling or page refresh

## Test Case 3: Relevant WebSocket Event Filtering

### Input
Receive a WebSocket event:
```json
{
  "type": "inventory_restocked",
  "payload": {
    "drug_name": "Paracetamol"
  }
}
```

### Expected Output
- Admin inventory view refreshes
- Triage queue should not trigger unnecessary fetch because the event is not relevant

### Pass/Fail Condition
- `PASSED` if only relevant pages refresh
- `FAILED` if unrelated pages make unnecessary API calls

## Test Case 4: WebSocket Reconnect

### Input
- Open Admin page
- Stop backend temporarily
- Restart backend after a few seconds

### Expected Output
- WebSocket disconnects
- Reconnect is attempted after delay
- UI resumes receiving updates after reconnection

### Pass/Fail Condition
- `PASSED` if reconnect succeeds automatically without duplicates
- `FAILED` if user must reload the page manually

## Test Case 5: Polling Backoff

### Input
- Cause repeated API failures by temporarily stopping backend

### Expected Output
- Polling interval grows from `4s` to `6s` to `10s`
- After backend recovery and a successful fetch, interval resets to `4s`

### Pass/Fail Condition
- `PASSED` if interval backs off and resets correctly
- `FAILED` if polling stays aggressive or creates overlapping requests

## JavaScript WebSocket Test Example
```javascript
const socket = new WebSocket("ws://127.0.0.1:8000/ws/updates/");

socket.onopen = () => {
  console.log("CONNECTED");
};

socket.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);
    console.log("MESSAGE RECEIVED", data);
    console.log("PASSED");
  } catch (error) {
    console.log("FAILED", error);
  }
};

socket.onerror = (error) => {
  console.log("FAILED", error);
};
```

## Python API + WebSocket Verification Script
```python
import asyncio
import json
import websockets

WS_URL = "ws://127.0.0.1:8000/ws/updates/"

async def main():
    try:
        async with websockets.connect(WS_URL) as websocket:
            message = await asyncio.wait_for(websocket.recv(), timeout=15)
            payload = json.loads(message)
            if "type" in payload:
                print("PASSED")
            else:
                print("FAILED", payload)
    except Exception as exc:
        print("FAILED", str(exc))

asyncio.run(main())
```

## High-Load / Multi-User Simulation

### Goal
Simulate `100` concurrent users subscribed to updates while some users trigger workflow actions.

### Expected Outcome
- Connections stay stable
- No reconnect storm
- No duplicate listeners
- Relevant pages refresh without full-page reloads

### Concurrency Script Skeleton
```python
import asyncio
import websockets

WS_URL = "ws://127.0.0.1:8000/ws/updates/"

async def listen(idx):
    try:
        async with websockets.connect(WS_URL) as websocket:
            await asyncio.wait_for(websocket.recv(), timeout=20)
            return True, idx
    except Exception:
        return False, idx

async def main():
    tasks = [listen(i) for i in range(100)]
    results = await asyncio.gather(*tasks)
    failures = [result for result in results if not result[0]]
    if failures:
        print("FAILED", failures[:5])
    else:
        print("PASSED")

asyncio.run(main())
```

## Manual Verification Checklist
- Open nurse page in one browser
- Open registration page in another browser
- Register patient
- Confirm nurse page updates automatically
- Complete triage
- Confirm doctor page updates automatically
- Complete consultation
- Confirm pharmacy page updates automatically
- Dispense drugs
- Confirm admin dashboard reflects changes

## Notes
- Polling remains the fallback if websocket events are temporarily unavailable
- WebSocket is used to improve speed and multi-user coordination, not replace all API validation
- Refresh-after-action is required so the acting user sees changes instantly even before the broadcast arrives
