import frappe
from frappe.model.document import Document
from frappe.utils import cint


class TourPackage(Document):
    def validate(self):
        if cint(self.duration_days) and not cint(self.duration_nights):
            self.duration_nights = max(0, cint(self.duration_days) - 1)
