frappe.ui.form.on("Tour Package Booking", {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            if (frm.doc.status !== "Completed") {
                frm.add_custom_button(__("Mark Completed"), () => set_status(frm, "Completed"));
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
            frm.dashboard.add_indicator(
                __("Outstanding: {0}", [format_currency(frm.doc.outstanding_amount, "OMR")]),
                frm.doc.outstanding_amount > 0 ? "orange" : "green"
            );
        }
    },
    onload(frm) {
        frm.set_query("tour_departure", () => ({
            filters: {
                tour_package: frm.doc.tour_package,
                status: ["in", ["Scheduled", "Confirmed"]],
            },
        }));
    },
    tour_package(frm) {
        frm.set_value("tour_departure", null);
    },
});

function set_status(frm, status) {
    frappe.call({
        method: "rental_tour_booking.rental_tour_booking.doctype.tour_package_booking.tour_package_booking.mark_status",
        args: { name: frm.doc.name, status },
        callback: () => frm.reload_doc(),
    });
}

function make_payment(frm) {
    frappe.new_doc("Booking Payment", {
        booking_type: "Tour Package",
        tour_package_booking: frm.doc.name,
        amount: frm.doc.outstanding_amount,
    });
}

function make_invoice(frm) {
    frappe.call({
        method: "rental_tour_booking.integrations.sales_invoice.make_invoice",
        args: { booking_type: "Tour Package", booking_name: frm.doc.name },
        freeze: true,
        freeze_message: __("Creating Sales Invoice…"),
        callback: () => frm.reload_doc(),
    });
}
