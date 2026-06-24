import frappe


ROLES = ["Rental Manager", "Rental Agent", "Tour Manager"]


def after_install():
    create_roles()
    setup_settings()
    frappe.db.commit()
    print("Rental & Tours: post-install setup complete.")


def create_roles():
    for role in ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role,
                "desk_access": 1,
            }).insert(ignore_permissions=True)


def setup_settings():
    settings = frappe.get_single("Rental Tour Settings")
    if not settings.default_currency:
        if frappe.db.exists("Currency", "OMR"):
            settings.default_currency = "OMR"
    if settings.vat_rate in (None, ""):
        settings.vat_rate = 5
    if settings.enable_online_booking in (None, ""):
        settings.enable_online_booking = 1
    if not settings.default_terms:
        settings.default_terms = (
            "<p>1. The renter must hold a valid driving licence.</p>"
            "<p>2. A refundable security deposit applies to all rentals.</p>"
            "<p>3. Fuel is charged on a like-for-like return basis.</p>"
            "<p>4. Cancellations within 24 hours may incur a fee.</p>"
        )
    settings.save(ignore_permissions=True)
