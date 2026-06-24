import frappe
from frappe.utils import nowdate, now_datetime


def mark_overdue_returns():
    """Notify on active rentals whose drop-off time has passed."""
    overdue = frappe.get_all(
        "Car Rental Booking",
        filters={
            "docstatus": 1,
            "status": ["in", ["Confirmed", "Active"]],
            "dropoff_datetime": ["<", now_datetime()],
        },
        fields=["name", "customer_name", "vehicle"],
    )
    for b in overdue:
        frappe.publish_realtime(
            "rental_overdue",
            {"booking": b.name, "vehicle": b.vehicle, "customer": b.customer_name},
        )


def close_past_departures():
    """Mark departures whose date has passed as Departed."""
    frappe.db.sql(
        """UPDATE `tabTour Departure`
           SET status = 'Departed'
           WHERE departure_date < %s
             AND status IN ('Scheduled', 'Confirmed', 'Full')""",
        nowdate(),
    )
    frappe.db.commit()
