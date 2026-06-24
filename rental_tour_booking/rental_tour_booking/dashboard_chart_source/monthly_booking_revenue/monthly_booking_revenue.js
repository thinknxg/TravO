frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Monthly Booking Revenue"] = {
    method: "rental_tour_booking.rental_tour_booking.dashboard_chart_source.monthly_booking_revenue.monthly_booking_revenue.get",
    filters: [],
};
