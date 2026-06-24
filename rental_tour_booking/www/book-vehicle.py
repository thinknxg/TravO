import frappe
from frappe import _


def get_context(context):
    context.no_cache = 1
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=" + (frappe.request.full_path or "/vehicles")
        raise frappe.Redirect

    vehicle = frappe.form_dict.get("vehicle")
    context.title = "Confirm your rental"
    context.currency = frappe.db.get_single_value("Rental Tour Settings", "default_currency") or "OMR"
    context.locations = frappe.get_all(
        "Rental Location", filters={"is_active": 1}, fields=["name", "location_name"],
        order_by="location_name",
    )
    context.vehicle = None
    if vehicle and frappe.db.exists("Rental Vehicle", vehicle):
        v = frappe.db.get_value(
            "Rental Vehicle", vehicle,
            ["name", "vehicle_name", "vehicle_category", "make", "model", "year",
             "transmission", "fuel_type", "seating_capacity", "daily_rate",
             "security_deposit", "status", "image"], as_dict=True,
        )
        context.vehicle = v
    return context
