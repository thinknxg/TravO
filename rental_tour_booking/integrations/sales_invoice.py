import frappe
from frappe import _
from frappe.utils import flt, nowdate


BOOKING_MAP = {
    "Car Rental": ("Car Rental Booking", "rental_item"),
    "Tour Package": ("Tour Package Booking", "tour_item"),
}


def _erpnext_ready():
    return "erpnext" in frappe.get_installed_apps()


def _settings():
    return frappe.get_cached_doc("Rental Tour Settings")


@frappe.whitelist()
def make_invoice(booking_type, booking_name):
    """Form-button entry point: create (or return existing) Sales Invoice."""
    if not _erpnext_ready():
        frappe.throw(_("ERPNext is not installed on this site, so Sales Invoices are unavailable."))
    doctype, item_field = BOOKING_MAP[booking_type]
    doc = frappe.get_doc(doctype, booking_name)

    if doc.get("sales_invoice") and frappe.db.exists("Sales Invoice", doc.sales_invoice):
        frappe.msgprint(_("Sales Invoice {0} already exists.").format(doc.sales_invoice))
        return doc.sales_invoice

    si_name = _build_invoice(doc, doctype, item_field)
    return si_name


def create_for_booking(doc, method=None):
    """doc_events on_submit hook: auto-create if enabled in settings."""
    if not _erpnext_ready():
        return
    settings = _settings()
    if not settings.get("create_sales_invoice"):
        return
    if doc.get("sales_invoice"):
        return
    booking_type = "Car Rental" if doc.doctype == "Car Rental Booking" else "Tour Package"
    _, item_field = BOOKING_MAP[booking_type]
    try:
        _build_invoice(doc, doc.doctype, item_field)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Auto Sales Invoice creation failed")
        frappe.msgprint(_("Booking submitted, but the Sales Invoice could not be created automatically. "
                          "You can create it manually from the booking."), alert=True)


def _build_invoice(doc, doctype, item_field):
    settings = _settings()
    item_code = settings.get(item_field)
    if not item_code:
        frappe.throw(_("Set the {0} under Rental Tour Settings before creating a Sales Invoice.")
                     .format(item_field.replace("_", " ").title()))

    company = settings.get("company") or frappe.defaults.get_global_default("company")
    if not company:
        frappe.throw(_("No default Company is configured."))

    description = _description(doc, doctype)

    si = frappe.new_doc("Sales Invoice")
    si.customer = doc.customer
    si.company = company
    si.posting_date = nowdate()
    si.due_date = nowdate()
    si.remarks = _("Auto-generated from {0} {1}").format(doctype, doc.name)
    if settings.get("cost_center"):
        si.cost_center = settings.cost_center

    si.append("items", {
        "item_code": item_code,
        "qty": 1,
        "rate": flt(doc.net_amount),
        "description": description,
    })

    # Apply a VAT tax template if configured, so totals mirror the booking
    if settings.get("sales_taxes_template"):
        si.taxes_and_charges = settings.sales_taxes_template
        try:
            from erpnext.controllers.accounts_controller import get_taxes_and_charges
            for tax in get_taxes_and_charges("Sales Taxes and Charges Template",
                                             settings.sales_taxes_template):
                si.append("taxes", tax)
        except Exception:
            pass

    si.flags.ignore_permissions = True
    si.insert()

    doc.db_set("sales_invoice", si.name)
    frappe.msgprint(_("Sales Invoice {0} created as a draft.").format(
        frappe.utils.get_link_to_form("Sales Invoice", si.name)), alert=True)
    return si.name


def _description(doc, doctype):
    if doctype == "Car Rental Booking":
        return _("Vehicle rental — {0} ({1} day(s)), {2} to {3}").format(
            doc.vehicle, doc.rental_days, doc.pickup_datetime, doc.dropoff_datetime)
    return _("Tour package — {0}{1}").format(
        doc.tour_package,
        ", departing " + str(doc.departure_date) if doc.get("departure_date") else "")
