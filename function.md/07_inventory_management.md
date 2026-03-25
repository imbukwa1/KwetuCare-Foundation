# 07. Inventory Management

## Function Description
This function manages stocked drugs in the Kwetu Care system. It allows authorized users to create inventory records, view available stock, update stock metadata, and restock existing drugs.

## Core Scope
- Create a new drug inventory record
- List inventory items
- Update inventory details
- Restock inventory
- Track stock quantity, amount, and reorder level
- Flag low-stock items

## Expected Behavior
- Admin can create, update, and restock inventory
- Admin, pharmacist, and doctor can view inventory
- Duplicate drug names should be rejected
- Restock should work even if current stock is not below reorder level
- Low-stock indicator should show `Yes` when `stock_quantity <= reorder_level`
- The `amount` field should display values like `500g`, `400ml`, etc.

## Main Endpoints
- `GET /api/inventory/`
- `POST /api/inventory/`
- `PUT /api/inventory/<id>/`
- `PATCH /api/inventory/<id>/`
- `POST /api/inventory/<id>/restock/`

## Test Case 1: Create New Inventory Item

### Input
```json
{
  "drug_name": "Amoxicillin",
  "amount": "500g",
  "stock_quantity": 12,
  "reorder_level": 5
}
```

### Expected Output
- HTTP `201 Created`
- Record saved successfully
- Drug appears in inventory list

### Pass/Fail Condition
- `PASSED` if the record is created and returned with the correct values
- `FAILED` if the API rejects valid input or stores wrong data

### curl Example
```bash
curl -X POST http://127.0.0.1:8000/api/inventory/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"drug_name\":\"Amoxicillin\",\"amount\":\"500g\",\"stock_quantity\":12,\"reorder_level\":5}"
```

## Test Case 2: Reject Duplicate Drug Name

### Input
Create a second item with the same drug name:
```json
{
  "drug_name": "Amoxicillin",
  "amount": "500g",
  "stock_quantity": 10,
  "reorder_level": 4
}
```

### Expected Output
- HTTP `400 Bad Request`
- Error message explaining the drug already exists

### Pass/Fail Condition
- `PASSED` if duplicate inventory creation is blocked
- `FAILED` if duplicate records are allowed

## Test Case 3: Restock Inventory

### Input
```json
{
  "quantity": 8
}
```

### Expected Output
- HTTP `200 OK`
- `stock_quantity` increases by `8`
- Low-stock flag updates correctly after restock

### Pass/Fail Condition
- `PASSED` if stock increases exactly by the restock amount
- `FAILED` if stock remains unchanged or increases incorrectly

### curl Example
```bash
curl -X POST http://127.0.0.1:8000/api/inventory/1/restock/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"quantity\":8}"
```

## Test Case 4: Reject Invalid Restock Quantity

### Input
```json
{
  "quantity": 0
}
```

### Expected Output
- HTTP `400 Bad Request`
- Validation error stating quantity must be greater than zero

### Pass/Fail Condition
- `PASSED` if invalid restock is blocked
- `FAILED` if zero or negative restock is accepted

## Test Case 5: Low-Stock Indicator

### Input
Inventory item:
```json
{
  "drug_name": "Paracetamol",
  "amount": "500g",
  "stock_quantity": 3,
  "reorder_level": 5
}
```

### Expected Output
- `low_stock = true` or UI shows `Yes`

### Pass/Fail Condition
- `PASSED` if low stock is correctly flagged when stock is at or below reorder level
- `FAILED` if the item is not flagged

## Python Test Script
```python
import requests

BASE = "http://127.0.0.1:8000/api"
TOKEN = "<ACCESS_TOKEN>"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

payload = {
    "drug_name": "Ibuprofen",
    "amount": "400g",
    "stock_quantity": 20,
    "reorder_level": 5,
}

response = requests.post(f"{BASE}/inventory/", json=payload, headers=headers, timeout=20)

if response.status_code == 201:
    print("PASSED")
else:
    print("FAILED", response.status_code, response.text)
```

## Concurrency / Load Test Approach
Use concurrent reads and controlled writes to verify the inventory API remains stable under load.

### High-Load Goal
- Simulate up to `100` concurrent users viewing inventory
- Simulate multiple restock actions from admins
- Ensure no duplicate records are created during concurrent writes

### Python Async Load Script
```python
import asyncio
import aiohttp

BASE = "http://127.0.0.1:8000/api/inventory/"
TOKEN = "<ACCESS_TOKEN>"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

async def fetch_inventory(session, idx):
    async with session.get(BASE, headers=HEADERS) as response:
        if response.status != 200:
            return False, idx, response.status
        return True, idx, response.status

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_inventory(session, i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        failures = [result for result in results if not result[0]]
        if failures:
            print("FAILED", failures[:5])
        else:
            print("PASSED")

asyncio.run(main())
```

## Manual Verification Checklist
- Create a drug successfully
- Confirm amount appears in admin inventory table
- Restock with a positive quantity
- Confirm stock increases instantly
- Confirm restock still works when stock is not low
- Try duplicate creation and verify validation error

## Notes
- Inventory names should be normalized consistently to avoid case-related mismatches
- Consultation and dispensing logic should always reference valid inventory names
