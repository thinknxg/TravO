import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Rent a Vehicle"
    context.categories = frappe.get_all(
        "Vehicle Category", filters={"is_active": 1}, fields=["name", "category_name"],
        order_by="category_name",
    )
    context.vehicles = frappe.get_all(
        "Rental Vehicle",
        filters={"is_active": 1, "status": "Available"},
        fields=["name", "vehicle_name", "vehicle_category", "make", "model", "year",
                "transmission", "fuel_type", "seating_capacity", "daily_rate", "image"],
        order_by="daily_rate asc",
    )
    context.currency = frappe.db.get_single_value("Rental Tour Settings", "default_currency") or "OMR"
    return context
