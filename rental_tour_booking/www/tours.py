import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Tour Packages"
    context.destinations = frappe.get_all(
        "Tour Destination", filters={"is_active": 1}, fields=["name", "destination_name"],
        order_by="destination_name",
    )
    context.packages = frappe.get_all(
        "Tour Package",
        filters={"is_active": 1},
        fields=["name", "package_name", "destination", "tour_type", "duration_days",
                "duration_nights", "price_per_person", "image"],
        order_by="price_per_person asc",
    )
    context.currency = frappe.db.get_single_value("Rental Tour Settings", "default_currency") or "OMR"
    return context
