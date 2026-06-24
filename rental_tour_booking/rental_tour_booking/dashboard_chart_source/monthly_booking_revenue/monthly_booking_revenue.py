import frappe
from frappe.utils import getdate, add_months, get_first_day, nowdate, flt


@frappe.whitelist()
def get(chart_name=None, chart=None, no_cache=None, filters=None, from_date=None,
        to_date=None, timespan=None, time_interval=None, heatmap_year=None):
    """Return last-12-months revenue split into Rentals and Tours datasets."""
    months = _last_months(12)
    start = months[0]["first_day"]

    rental = _monthly_totals("Car Rental Booking", start)
    tour = _monthly_totals("Tour Package Booking", start)

    labels = [m["label"] for m in months]
    rental_vals = [flt(rental.get(m["key"], 0), 2) for m in months]
    tour_vals = [flt(tour.get(m["key"], 0), 2) for m in months]

    return {
        "labels": labels,
        "datasets": [
            {"name": "Car Rentals", "values": rental_vals},
            {"name": "Tours", "values": tour_vals},
        ],
        "type": "bar",
    }


def _last_months(n):
    today = getdate(nowdate())
    out = []
    for i in range(n - 1, -1, -1):
        d = add_months(today, -i)
        fd = get_first_day(d)
        out.append({
            "key": fd.strftime("%Y-%m"),
            "label": fd.strftime("%b %Y"),
            "first_day": fd,
        })
    return out


def _monthly_totals(doctype, start):
    rows = frappe.db.sql(
        """
        SELECT DATE_FORMAT(COALESCE(booking_date, creation), '%%Y-%%m') AS ym,
               SUM(grand_total) AS total
        FROM `tab{dt}`
        WHERE docstatus = 1
          AND status != 'Cancelled'
          AND COALESCE(booking_date, creation) >= %(start)s
        GROUP BY ym
        """.format(dt=doctype),
        {"start": start},
        as_dict=True,
    )
    return {r.ym: flt(r.total) for r in rows}
