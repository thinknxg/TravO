# Rental &amp; Tours (`rental_tour_booking`)

A complete thinkNXG **v16** app for **Car Rental Booking** and **Tour Package Booking**, built for the GCC market (defaults: OMR currency, 5% VAT, Oman-oriented terms).

## What's inside

### Booking transactions (submittable)
- **Car Rental Booking** — vehicle + schedule, auto day-count, extras, discount, VAT, deposit, double-booking prevention, status lifecycle (Draft → Confirmed → Active → Completed / Cancelled).
- **Tour Package Booking** — package + departure, adult/child pricing, traveler manifest, seat allocation, VAT, lifecycle (Draft → Confirmed → Paid → Completed / Cancelled).
- **Booking Payment** — receipts against either booking type; auto-updates paid / outstanding on parent.

### Fleet masters
- **Rental Vehicle** (plate-named, status-tracked, rate fallback to category)
- **Vehicle Category** (default daily/weekly/monthly rates + deposit)
- **Rental Location** &middot; **Rental Extra** (per-day or flat add-ons)

### Tour masters
- **Tour Package** (itinerary + inclusions child tables, group/private/self-drive)
- **Tour Destination** &middot; **Tour Departure** (dated, seat-managed)

### Platform
- **Rental Tour Settings** (single) — company, currency, VAT rate, online-booking toggle, default terms.
- **Workspace** "Rental &amp; Tours" with shortcuts and cards.
- **Query reports**: Active Rentals, Upcoming Departures.
- **Roles**: Rental Manager, Rental Agent, Tour Manager (created on install).
- **Scheduled tasks**: overdue-return alerts, auto-close past departures.
- **Portal pages**: `/vehicles` and `/tours` catalogues + guest API for availability and booking requests.

## Key business logic
- **No double-booking**: overlapping-period check per vehicle on validate and via API.
- **Day count**: `< 24h` counts as 1 day, otherwise day difference (configurable in `utils.py`).
- **Pricing**: `base + extras − discount = net`, `VAT = net × rate%`, `grand_total = net + VAT`.
- **Seats**: decremented on tour booking submit, restored on cancel; departure flips to `Full` at zero.
- **Vehicle status** auto-syncs (Rented on pickup, Available on completion/cancel).

## Install

```bash
# from your bench directory
bench get-app rental_tour_booking /path/to/rental_tour_booking
bench --site yoursite.local install-app rental_tour_booking
bench --site yoursite.local migrate
bench build && bench restart
```

`after_install` creates the custom roles and seeds **Rental Tour Settings** (OMR, 5% VAT). Adjust currency/VAT under **Rental Tour Settings** if you operate in UAE/KSA/Bahrain.

## Public API (whitelisted)
- `rental_tour_booking.api.list_available_vehicles(category, location)`
- `rental_tour_booking.api.list_tour_packages(destination, tour_type)`
- `rental_tour_booking.api.check_vehicle_availability(vehicle, pickup_datetime, dropoff_datetime)`
- `rental_tour_booking.api.create_rental_request(...)` (auth)
- `rental_tour_booking.api.create_tour_request(...)` (auth)

## Layout
```
rental_tour_booking/
├── hooks.py · api.py · tasks.py · utils.py
├── setup/install.py
├── www/{vehicles,tours}.{html,py}
└── rental_tour_booking/
    ├── doctype/        (15 DocTypes)
    ├── report/         (Active Rentals, Upcoming Departures)
    └── workspace/
```

## Customer portal &amp; accounting

- **Online booking** (login-gated): `/vehicles` &amp; `/tours` catalogues → `/book-vehicle` / `/book-tour` checkout (live quote + availability/seat check) → Draft booking → `/my-bookings`.
- **Self-service PDFs**: customers download their **Rental Agreement** / **Tour Voucher** from `/my-bookings` via `api.download_booking_pdf` (ownership-checked).
- **Sales Invoice bridge** (ERPNext): a **Create Sales Invoice** button on each booking, plus optional auto-creation on submit (toggle in **Rental Tour Settings**). Configure the rental/tour service Items, cost center, and a VAT tax template; the draft SI is linked back on the booking. Guarded so the app still installs without ERPNext.

---
Built by **Kreatao** for thinkNXG v16.
