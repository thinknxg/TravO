import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, get_datetime
from rental_tour_booking.utils import get_default_vat_rate, get_default_terms, rental_day_count


class CarRentalBooking(Document):
    def validate(self):
        self.set_defaults()
        self.validate_dates()
        self.check_vehicle_availability()
        self.calculate_charges()
        self.set_outstanding()

    def set_defaults(self):
        if not self.booking_date:
            self.booking_date = frappe.utils.today()
        if self.vat_rate in (None, ""):
            self.vat_rate = get_default_vat_rate()
        if not self.terms:
            self.terms = get_default_terms()
        if not self.dropoff_location:
            self.dropoff_location = self.pickup_location

    def validate_dates(self):
        if self.pickup_datetime and self.dropoff_datetime:
            if get_datetime(self.dropoff_datetime) <= get_datetime(self.pickup_datetime):
                frappe.throw(_("Drop-off must be after pick-up."))
        self.rental_days = rental_day_count(self.pickup_datetime, self.dropoff_datetime)

    def check_vehicle_availability(self):
        if not (self.vehicle and self.pickup_datetime and self.dropoff_datetime):
            return
        clash = frappe.db.sql(
            """
            SELECT name FROM `tabCar Rental Booking`
            WHERE vehicle = %(vehicle)s
              AND name != %(name)s
              AND docstatus < 2
              AND status NOT IN ('Cancelled', 'Completed')
              AND pickup_datetime < %(dropoff)s
              AND dropoff_datetime > %(pickup)s
            LIMIT 1
            """,
            {
                "vehicle": self.vehicle,
                "name": self.name or "New",
                "pickup": self.pickup_datetime,
                "dropoff": self.dropoff_datetime,
            },
        )
        if clash:
            frappe.throw(
                _("Vehicle {0} is already booked in this period (booking {1}).").format(
                    frappe.bold(self.vehicle), clash[0][0]
                )
            )

    def calculate_charges(self):
        days = cint(self.rental_days) or 1
        self.base_amount = flt(self.daily_rate) * days

        extras_total = 0.0
        for row in self.extras:
            if row.charge_type == "Per Day":
                qty = cint(row.qty_days) or days
                row.amount = flt(row.rate) * qty
            else:
                row.amount = flt(row.rate) * (cint(row.qty_days) or 1)
            extras_total += flt(row.amount)
        self.extras_amount = extras_total

        self.net_amount = flt(self.base_amount) + flt(self.extras_amount) - flt(self.discount_amount)
        self.vat_amount = flt(self.net_amount) * flt(self.vat_rate) / 100.0
        self.grand_total = flt(self.net_amount) + flt(self.vat_amount)

    def set_outstanding(self):
        self.outstanding_amount = flt(self.grand_total) - flt(self.paid_amount)

    def before_submit(self):
        if self.status == "Draft":
            self.status = "Confirmed"

    def on_submit(self):
        self.update_vehicle_status("Rented")

    def on_cancel(self):
        self.status = "Cancelled"
        self.update_vehicle_status("Available")

    def update_vehicle_status(self, status):
        if self.vehicle and self.status not in ("Completed",):
            frappe.db.set_value("Rental Vehicle", self.vehicle, "status", status)

    def refresh_payment_totals(self):
        paid = frappe.db.sql(
            """SELECT COALESCE(SUM(amount), 0) FROM `tabBooking Payment`
               WHERE car_rental_booking = %s AND docstatus = 1""",
            self.name,
        )[0][0]
        self.db_set("paid_amount", flt(paid))
        self.db_set("outstanding_amount", flt(self.grand_total) - flt(paid))


@frappe.whitelist()
def mark_status(name, status):
    doc = frappe.get_doc("Car Rental Booking", name)
    if doc.docstatus != 1:
        frappe.throw(_("Booking must be submitted first."))
    allowed = {"Active", "Completed"}
    if status not in allowed:
        frappe.throw(_("Invalid status transition."))
    doc.db_set("status", status)
    if status == "Active":
        frappe.db.set_value("Rental Vehicle", doc.vehicle, "status", "Rented")
    elif status == "Completed":
        frappe.db.set_value("Rental Vehicle", doc.vehicle, "status", "Available")
    return status
