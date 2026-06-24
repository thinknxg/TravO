import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, add_days, getdate


class TourDeparture(Document):
    def validate(self):
        self.set_return_date()
        self.init_seats()

    def set_return_date(self):
        if self.tour_package and self.departure_date:
            days = cint(frappe.db.get_value("Tour Package", self.tour_package, "duration_days"))
            if days:
                self.return_date = add_days(getdate(self.departure_date), days - 1)

    def init_seats(self):
        if self.is_new() or self.available_seats in (None, ""):
            self.available_seats = cint(self.total_seats)
        if cint(self.available_seats) > cint(self.total_seats):
            frappe.throw(_("Available seats cannot exceed total seats."))
