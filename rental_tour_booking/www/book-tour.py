import frappe
from frappe import _


def get_context(context):
    context.no_cache = 1
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=" + (frappe.request.full_path or "/tours")
        raise frappe.Redirect

    package = frappe.form_dict.get("package")
    context.title = "Book your tour"
    context.currency = frappe.db.get_single_value("Rental Tour Settings", "default_currency") or "OMR"
    context.package = None
    if package and frappe.db.exists("Tour Package", package):
        p = frappe.db.get_value(
            "Tour Package", package,
            ["name", "package_name", "destination", "tour_type", "duration_days",
             "duration_nights", "price_per_person", "child_price", "min_pax", "max_pax", "image"],
            as_dict=True,
        )
        context.package = p
        context.departures = frappe.get_all(
            "Tour Departure",
            filters={"tour_package": package, "status": ["in", ["Scheduled", "Confirmed"]],
                     "departure_date": [">=", frappe.utils.nowdate()], "available_seats": [">", 0]},
            fields=["name", "departure_date", "return_date", "available_seats", "price_per_person"],
            order_by="departure_date asc",
        )
    return context
