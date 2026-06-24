app_name = "rental_tour_booking"
app_title = "Rental & Tours"
app_publisher = "Kreatao"
app_description = "Car Rental & Tour Package Booking management for Frappe v16 (GCC-ready)"
app_email = "dev@kreatao.com"
app_license = "MIT"
app_version = "0.0.1"
required_apps = ["frappe"]

# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------
after_install = "rental_tour_booking.setup.install.after_install"

# ---------------------------------------------------------------------------
# Document Events
# ---------------------------------------------------------------------------
doc_events = {
    "Car Rental Booking": {
        "on_submit": "rental_tour_booking.integrations.sales_invoice.create_for_booking",
    },
    "Tour Package Booking": {
        "on_submit": "rental_tour_booking.integrations.sales_invoice.create_for_booking",
    },
}

# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------
scheduler_events = {
    "daily": [
        "rental_tour_booking.tasks.mark_overdue_returns",
        "rental_tour_booking.tasks.close_past_departures",
    ]
}

# ---------------------------------------------------------------------------
# Website / Portal
# ---------------------------------------------------------------------------
website_route_rules = [
    {"from_route": "/vehicles", "to_route": "vehicles"},
    {"from_route": "/tours", "to_route": "tours"},
    {"from_route": "/book-vehicle", "to_route": "book-vehicle"},
    {"from_route": "/book-tour", "to_route": "book-tour"},
    {"from_route": "/my-bookings", "to_route": "my-bookings"},
]

# Logged-in customer portal menu
standard_portal_menu_items = [
    {"title": "My Bookings", "route": "/my-bookings", "reference_doctype": "",
     "role": "Customer"},
    {"title": "Rent a Vehicle", "route": "/vehicles", "reference_doctype": "", "role": ""},
    {"title": "Browse Tours", "route": "/tours", "reference_doctype": "", "role": ""},
]

# Fixtures (custom roles created in installer; keep empty to avoid over-export)
fixtures = []
