import frappe
from frappe.utils import flt, date_diff, getdate


def get_settings():
    return frappe.get_cached_doc("Rental Tour Settings")


def get_default_vat_rate():
    try:
        rate = flt(get_settings().vat_rate)
    except Exception:
        rate = 0.0
    return rate


def get_default_terms():
    try:
        return get_settings().default_terms
    except Exception:
        return None


def rental_day_count(pickup, dropoff):
    """Inclusive-ish day count: a rental of <24h counts as 1 day, then rounds up."""
    if not pickup or not dropoff:
        return 0
    diff = date_diff(getdate(dropoff), getdate(pickup))
    return max(1, int(diff) if diff else 1)
