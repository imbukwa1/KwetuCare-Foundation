from test_helpers import CaseCollector, api_request, auth_token_for, create_inventory, ensure_backend, print_summary


def main():
    collector = CaseCollector("07 Inventory Management Tests")
    ok, message = ensure_backend()
    collector.check("backend_ping", ok, message)
    if not ok:
        return print_summary("07 Inventory Management Tests", collector)

    admin_token, _ = auth_token_for("admin", "inventory_admin")
    doctor_token, _ = auth_token_for("general_doctor", "inventory_doc")
    if not admin_token or not doctor_token:
        collector.check("role_logins", False, "admin or doctor login failed")
        return print_summary("07 Inventory Management Tests", collector)
    collector.check("role_logins", True, "admin and doctor ready")

    status, data = create_inventory(admin_token, drug_name="Ibuprofen", amount="400mg", stock_quantity=15, reorder_level=4, expiry_date="2027-11-30")
    inventory_id = data.get("id") if isinstance(data, dict) else None
    collector.check("create_inventory_batch", status in (200, 201) and inventory_id, f"status={status}")

    status, data = api_request("GET", "/inventory/", token=admin_token)
    collector.check("inventory_list", status == 200 and isinstance(data, list), f"status={status}")

    status, data = api_request("POST", f"/inventory/{inventory_id}/restock/", {"quantity": 5, "expiry_date": "2027-12-31"}, token=admin_token)
    collector.check("inventory_restock", status == 200, f"status={status}")

    status, data = api_request("GET", "/inventory/available/", token=doctor_token)
    labels = [item.get("label", "") for item in data] if isinstance(data, list) else []
    collector.check("available_drugs_visible_to_doctor", status == 200 and any("Ibuprofen" in item.get("drug_name", "") for item in data), f"status={status}")
    collector.check("available_drug_labels", status == 200 and any("400mg" in label for label in labels), str(labels[:3]))
    return print_summary("07 Inventory Management Tests", collector)


if __name__ == "__main__":
    raise SystemExit(main())
