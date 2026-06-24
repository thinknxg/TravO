import frappe
from frappe import _
from frappe.utils import flt, cint
from rental_tour_booking.utils import rental_day_count, get_default_vat_rate


def _online_enabled():
    if not cint(frappe.db.get_single_value("Rental Tour Settings", "enable_online_booking")):
        frappe.throw(_("Online booking is currently disabled."))


@frappe.whitelist(allow_guest=True)
def list_available_vehicles(category=None, location=None):
    filters = {"is_active": 1, "status": "Available"}
    if category:
        filters["vehicle_category"] = category
    if location:
        filters["location"] = location
    return frappe.get_all(
        "Rental Vehicle",
        filters=filters,
        fields=["name", "vehicle_name", "vehicle_category", "make", "model", "year",
                "transmission", "fuel_type", "seating_capacity", "daily_rate", "image", "location"],
        order_by="daily_rate asc",
    )


@frappe.whitelist(allow_guest=True)
def list_tour_packages(destination=None, tour_type=None):
    filters = {"is_active": 1}
    if destination:
        filters["destination"] = destination
    if tour_type:
        filters["tour_type"] = tour_type
    return frappe.get_all(
        "Tour Package",
        filters=filters,
        fields=["name", "package_name", "destination", "tour_type", "duration_days",
                "duration_nights", "price_per_person", "child_price", "image"],
        order_by="price_per_person asc",
    )


@frappe.whitelist(allow_guest=True)
def check_vehicle_availability(vehicle, pickup_datetime, dropoff_datetime):
    clash = frappe.db.count(
        "Car Rental Booking",
        {
            "vehicle": vehicle,
            "docstatus": ["<", 2],
            "status": ["not in", ["Cancelled", "Completed"]],
            "pickup_datetime": ["<", dropoff_datetime],
            "dropoff_datetime": [">", pickup_datetime],
        },
    )
    days = rental_day_count(pickup_datetime, dropoff_datetime)
    rate = flt(frappe.db.get_value("Rental Vehicle", vehicle, "daily_rate"))
    net = rate * days
    vat = net * get_default_vat_rate() / 100.0
    return {
        "available": clash == 0,
        "rental_days": days,
        "daily_rate": rate,
        "estimated_total": net + vat,
    }


@frappe.whitelist()
def create_rental_request(vehicle, pickup_location, pickup_datetime, dropoff_datetime,
                          dropoff_location=None, customer=None):
    """Authenticated portal endpoint to create a Draft rental booking."""
    _online_enabled()
    customer = customer or _portal_customer()
    doc = frappe.get_doc({
        "doctype": "Car Rental Booking",
        "customer": customer,
        "vehicle": vehicle,
        "pickup_location": pickup_location,
        "dropoff_location": dropoff_location or pickup_location,
        "pickup_datetime": pickup_datetime,
        "dropoff_datetime": dropoff_datetime,
    })
    doc.insert(ignore_permissions=True)
    return {"name": doc.name, "grand_total": doc.grand_total}


@frappe.whitelist()
def create_tour_request(tour_package, num_adults=1, num_children=0,
                        tour_departure=None, customer=None):
    """Authenticated portal endpoint to create a Draft tour booking."""
    _online_enabled()
    customer = customer or _portal_customer()
    doc = frappe.get_doc({
        "doctype": "Tour Package Booking",
        "customer": customer,
        "tour_package": tour_package,
        "tour_departure": tour_departure,
        "num_adults": cint(num_adults),
        "num_children": cint(num_children),
    })
    doc.insert(ignore_permissions=True)
    return {"name": doc.name, "grand_total": doc.grand_total}


def _portal_customer():
    """Return the Customer linked to the logged-in user, creating one if needed."""
    user = frappe.session.user
    if user == "Guest":
        frappe.throw(_("Please log in to continue."), frappe.PermissionError)

    customer = frappe.db.get_value("Customer", {"email_id": user}, "name")
    if customer:
        return customer

    # fall back to a customer whose name matches the contact, else create one
    full_name = frappe.utils.get_fullname(user) or user
    customer = frappe.db.get_value("Customer", {"customer_name": full_name}, "name")
    if customer:
        return customer

    try:
        doc = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": full_name,
            "customer_type": "Individual",
            "email_id": user,
            "customer_group": _default_link("Customer Group", "customer_group"),
            "territory": _default_link("Territory", "territory"),
        })
        doc.insert(ignore_permissions=True)
        return doc.name
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Portal customer creation failed")
        frappe.throw(_("We couldn't set up your customer profile automatically. Please contact us."))


def _default_link(doctype, default_key):
    val = frappe.defaults.get_global_default(default_key)
    if val and frappe.db.exists(doctype, val):
        return val
    # pick the first non-group leaf record as a safe default
    leaf = frappe.db.get_value(doctype, {"is_group": 0}, "name") if \
        frappe.get_meta(doctype).has_field("is_group") else frappe.db.get_value(doctype, {}, "name")
    return leaf


@frappe.whitelist(allow_guest=True)
def list_departures(tour_package):
    return frappe.get_all(
        "Tour Departure",
        filters={
            "tour_package": tour_package,
            "status": ["in", ["Scheduled", "Confirmed"]],
            "departure_date": [">=", frappe.utils.nowdate()],
            "available_seats": [">", 0],
        },
        fields=["name", "departure_date", "return_date", "available_seats", "price_per_person"],
        order_by="departure_date asc",
    )


@frappe.whitelist()
def get_my_bookings():
    customer = _portal_customer()
    rentals = frappe.get_all(
        "Car Rental Booking",
        filters={"customer": customer},
        fields=["name", "vehicle", "pickup_datetime", "dropoff_datetime", "status",
                "grand_total", "outstanding_amount"],
        order_by="creation desc",
    )
    tours = frappe.get_all(
        "Tour Package Booking",
        filters={"customer": customer},
        fields=["name", "tour_package", "departure_date", "status",
                "grand_total", "outstanding_amount"],
        order_by="creation desc",
    )
    return {"rentals": rentals, "tours": tours}


# Print format used per booking type for the customer-facing PDF
_PDF_MAP = {
    "Car Rental": ("Car Rental Booking", "Rental Agreement"),
    "Tour Package": ("Tour Package Booking", "Tour Voucher"),
}


@frappe.whitelist()
def download_booking_pdf(booking_type, name):
    """Stream the agreement/voucher PDF for a booking owned by the logged-in customer."""
    if booking_type not in _PDF_MAP:
        frappe.throw(_("Unknown booking type."))
    doctype, print_format = _PDF_MAP[booking_type]

    customer = _portal_customer()
    owner = frappe.db.get_value(doctype, name, "customer")
    if not owner or owner != customer:
        frappe.throw(_("You are not allowed to access this document."), frappe.PermissionError)

    doc = frappe.get_doc(doctype, name)
    pdf = frappe.get_print(doctype, name, print_format=print_format, doc=doc, as_pdf=True)
    frappe.local.response.filename = "{0}.pdf".format(name)
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "pdf"
