from test_helpers import CaseCollector, api_request, auth_token_for, create_inventory, ensure_backend, print_summary


def main():
    collector = CaseCollector("12 Inventory Categories And Visibility Tests")
    ok, message = ensure_backend()
    collector.check("backend_ping", ok, message)
    if not ok:
        return print_summary("12 Inventory Categories And Visibility Tests", collector)

    admin_token, _ = auth_token_for("admin", "inventory_category_admin")
    doctor_token, _ = auth_token_for("general_doctor", "inventory_category_doctor")
    collector.check("role_logins", bool(admin_token and doctor_token), "admin and doctor ready")
    if not admin_token or not doctor_token:
        return print_summary("12 Inventory Categories And Visibility Tests", collector)

    status, data = api_request(
        "POST",
        "/inventory/",
        {
            "drug_name": "Amoxicillin",
            "category": "antibiotics",
            "amount": "500mg",
            "stock_quantity": 18,
            "reorder_level": 4,
            "expiry_date": "2027-12-31",
        },
        token=admin_token,
    )
    collector.check("create_antibiotic_inventory", status in (200, 201), f"status={status}")

    status, data = create_inventory(
        admin_token,
        drug_name="Cetirizine",
        amount="10mg",
        stock_quantity=12,
        reorder_level=3,
        expiry_date="2027-10-31",
    )
    collector.check("create_second_inventory_item", status in (200, 201), f"status={status}")

    status, data = api_request("GET", "/inventory/available/", token=doctor_token)
    available = data if isinstance(data, list) else []
    antibiotic_entry = next((item for item in available if item.get("drug_name") == "Amoxicillin"), None)
    collector.check("available_inventory_list", status == 200 and bool(available), f"status={status}")
    collector.check(
        "category_present_in_available_drugs",
        bool(antibiotic_entry and antibiotic_entry.get("category") == "antibiotics"),
        str(antibiotic_entry),
    )
    collector.check(
        "category_label_present_in_available_drugs",
        bool(antibiotic_entry and antibiotic_entry.get("category_label") == "Antibiotics"),
        str(antibiotic_entry),
    )
    collector.check(
        "inventory_labels_include_units",
        any("500mg" in item.get("label", "") or "10mg" in item.get("label", "") for item in available),
        str([item.get("label") for item in available[:5]]),
    )
    return print_summary("12 Inventory Categories And Visibility Tests", collector)


if __name__ == "__main__":
    raise SystemExit(main())
