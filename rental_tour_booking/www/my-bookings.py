import frappe


def get_context(context):
    context.no_cache = 1
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/my-bookings"
        raise frappe.Redirect

    context.title = "My Bookings"
    context.currency = frappe.db.get_single_value("Rental Tour Settings", "default_currency") or "OMR"

    customer = frappe.db.get_value("Customer", {"email_id": frappe.session.user}, "name")
    context.rentals = []
    context.tours = []
    if customer:
        context.rentals = frappe.get_all(
            "Car Rental Booking", filters={"customer": customer},
            fields=["name", "vehicle", "pickup_datetime", "dropoff_datetime",
                    "status", "grand_total", "outstanding_amount"],
            order_by="creation desc",
        )
        context.tours = frappe.get_all(
            "Tour Package Booking", filters={"customer": customer},
            fields=["name", "tour_package", "departure_date",
                    "status", "grand_total", "outstanding_amount"],
            order_by="creation desc",
        )
    return context
