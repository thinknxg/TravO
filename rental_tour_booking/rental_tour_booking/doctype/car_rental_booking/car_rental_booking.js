frappe.ui.form.on("Car Rental Booking", {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            if (["Confirmed"].includes(frm.doc.status)) {
                frm.add_custom_button(__("Mark Active (Picked Up)"), () => set_status(frm, "Active"));
            }
            if (["Confirmed", "Active"].includes(frm.doc.status)) {
                frm.add_custom_button(__("Mark Completed (Returned)"), () => set_status(frm, "Completed"));
            }
            if (frm.doc.outstanding_amount > 0) {
                frm.add_custom_button(__("Collect Payment"), () => make_payment(frm), __("Create"));
            }
            if (frm.doc.sales_invoice) {
                frm.add_custom_button(__("View Sales Invoice"), () =>
                    frappe.set_route("Form", "Sales Invoice", frm.doc.sales_invoice));
            } else {
                frm.add_custom_button(__("Sales Invoice"), () => make_invoice(frm), __("Create"));
            }
        }
        render_summary(frm);
    },
    vehicle(frm) {
        if (frm.doc.vehicle) {
            frappe.db.get_value("Rental Vehicle", frm.doc.vehicle, "status").then((r) => {
                if (r.message && r.message.status !== "Available") {
                    frappe.msgprint(__("Note: vehicle status is currently {0}.", [r.message.status]));
                }
            });
        }
    },
    pickup_datetime: recalc,
    dropoff_datetime: recalc,
    daily_rate: recalc,
    discount_amount: recalc,
    vat_rate: recalc,
    onload(frm) {
        frm.set_query("vehicle", () => ({ filters: { is_active: 1 } }));
    },
});

frappe.ui.form.on("Rental Booking Extra", {
    extra: recalc_extras,
    rate: recalc_extras,
    qty_days: recalc_extras,
    extras_remove: recalc_extras,
});

function recalc(frm) {
    frm.trigger("validate_client_total");
}

function recalc_extras(frm) {
    frm.dirty();
}

function set_status(frm, status) {
    frappe.call({
        method: "rental_tour_booking.rental_tour_booking.doctype.car_rental_booking.car_rental_booking.mark_status",
        args: { name: frm.doc.name, status },
        callback: () => frm.reload_doc(),
    });
}

function make_payment(frm) {
    frappe.new_doc("Booking Payment", {
        booking_type: "Car Rental",
        car_rental_booking: frm.doc.name,
        amount: frm.doc.outstanding_amount,
    });
}

function make_invoice(frm) {
    frappe.call({
        method: "rental_tour_booking.integrations.sales_invoice.make_invoice",
        args: { booking_type: "Car Rental", booking_name: frm.doc.name },
        freeze: true,
        freeze_message: __("Creating Sales Invoice…"),
        callback: () => frm.reload_doc(),
    });
}

function render_summary(frm) {
    if (frm.doc.docstatus === 1 && frm.doc.grand_total) {
        const c = frm.doc.currency || "OMR";
        frm.dashboard.add_indicator(
            __("Outstanding: {0}", [format_currency(frm.doc.outstanding_amount, c)]),
            frm.doc.outstanding_amount > 0 ? "orange" : "green"
        );
    }
}
