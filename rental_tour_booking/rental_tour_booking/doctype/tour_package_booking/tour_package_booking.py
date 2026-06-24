import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint
from rental_tour_booking.utils import get_default_vat_rate, get_default_terms


class TourPackageBooking(Document):
    def validate(self):
        self.set_defaults()
        self.validate_pax()
        self.calculate_charges()
        self.set_outstanding()

    def set_defaults(self):
        if not self.booking_date:
            self.booking_date = frappe.utils.today()
        if self.vat_rate in (None, ""):
            self.vat_rate = get_default_vat_rate()
        if not self.terms:
            self.terms = get_default_terms()

    def validate_pax(self):
        total_pax = cint(self.num_adults) + cint(self.num_children)
        if total_pax < 1:
            frappe.throw(_("At least one traveler is required."))

        pkg = frappe.db.get_value(
            "Tour Package", self.tour_package, ["min_pax", "max_pax"], as_dict=True
        )
        if pkg:
            if pkg.min_pax and total_pax < cint(pkg.min_pax):
                frappe.throw(_("Minimum {0} travelers required for this package.").format(pkg.min_pax))
            if pkg.max_pax and total_pax > cint(pkg.max_pax):
                frappe.throw(_("Maximum {0} travelers allowed for this package.").format(pkg.max_pax))

        if self.tour_departure:
            avail = cint(frappe.db.get_value("Tour Departure", self.tour_departure, "available_seats"))
            # add back seats already held by this booking (on amend / re-validate)
            if self.docstatus == 1:
                pass
            if total_pax > avail and self.docstatus == 0:
                frappe.throw(
                    _("Only {0} seat(s) left on departure {1}.").format(avail, self.tour_departure)
                )

    def calculate_charges(self):
        adults_amt = flt(self.price_per_person) * cint(self.num_adults)
        child_amt = flt(self.child_price) * cint(self.num_children)
        self.base_amount = adults_amt + child_amt
        self.net_amount = flt(self.base_amount) - flt(self.discount_amount)
        self.vat_amount = flt(self.net_amount) * flt(self.vat_rate) / 100.0
        self.grand_total = flt(self.net_amount) + flt(self.vat_amount)

    def set_outstanding(self):
        self.outstanding_amount = flt(self.grand_total) - flt(self.paid_amount)

    def before_submit(self):
        if self.status == "Draft":
            self.status = "Confirmed"

    def on_submit(self):
        self.adjust_seats(-1)

    def on_cancel(self):
        self.status = "Cancelled"
        self.adjust_seats(1)

    def adjust_seats(self, direction):
        if not self.tour_departure:
            return
        pax = cint(self.num_adults) + cint(self.num_children)
        dep = frappe.get_doc("Tour Departure", self.tour_departure)
        dep.available_seats = cint(dep.available_seats) + (direction * pax)
        if dep.available_seats < 0:
            dep.available_seats = 0
        if dep.available_seats == 0 and direction < 0:
            dep.status = "Full"
        elif direction > 0 and dep.status == "Full":
            dep.status = "Confirmed"
        dep.save(ignore_permissions=True)

    def refresh_payment_totals(self):
        paid = frappe.db.sql(
            """SELECT COALESCE(SUM(amount), 0) FROM `tabBooking Payment`
               WHERE tour_package_booking = %s AND docstatus = 1""",
            self.name,
        )[0][0]
        self.db_set("paid_amount", flt(paid))
        self.db_set("outstanding_amount", flt(self.grand_total) - flt(paid))
        if flt(paid) >= flt(self.grand_total) and self.status == "Confirmed":
            self.db_set("status", "Paid")


@frappe.whitelist()
def mark_status(name, status):
    doc = frappe.get_doc("Tour Package Booking", name)
    if doc.docstatus != 1:
        frappe.throw(_("Booking must be submitted first."))
    if status not in {"Paid", "Completed"}:
        frappe.throw(_("Invalid status transition."))
    doc.db_set("status", status)
    return status
