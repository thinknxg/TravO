import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class BookingPayment(Document):
    def validate(self):
        self.set_customer()
        if flt(self.amount) <= 0:
            frappe.throw(_("Payment amount must be greater than zero."))

    def set_customer(self):
        if self.booking_type == "Car Rental" and self.car_rental_booking:
            self.customer = frappe.db.get_value(
                "Car Rental Booking", self.car_rental_booking, "customer"
            )
        elif self.booking_type == "Tour Package" and self.tour_package_booking:
            self.customer = frappe.db.get_value(
                "Tour Package Booking", self.tour_package_booking, "customer"
            )

    def on_submit(self):
        self.update_parent()

    def on_cancel(self):
        self.update_parent()

    def update_parent(self):
        if self.booking_type == "Car Rental" and self.car_rental_booking:
            frappe.get_doc("Car Rental Booking", self.car_rental_booking).refresh_payment_totals()
        elif self.booking_type == "Tour Package" and self.tour_package_booking:
            frappe.get_doc("Tour Package Booking", self.tour_package_booking).refresh_payment_totals()
