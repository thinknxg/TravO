import frappe
from frappe.model.document import Document
from frappe.utils import flt


class RentalVehicle(Document):
    def validate(self):
        if not flt(self.daily_rate) and self.vehicle_category:
            cat = frappe.db.get_value(
                "Vehicle Category", self.vehicle_category,
                ["daily_rate", "weekly_rate", "monthly_rate", "security_deposit"],
                as_dict=True,
            )
            if cat:
                self.daily_rate = cat.daily_rate
                self.weekly_rate = self.weekly_rate or cat.weekly_rate
                self.monthly_rate = self.monthly_rate or cat.monthly_rate
                self.security_deposit = self.security_deposit or cat.security_deposit
