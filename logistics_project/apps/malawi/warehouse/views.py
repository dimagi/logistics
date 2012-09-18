from django.conf import settings
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib import messages

from logistics.decorators import place_in_request

from logistics_project.apps.malawi.warehouse.report_utils import datespan_default

from logistics_project.apps.malawi.warehouse.report_views import dashboard, emergency_orders,\
    order_fill_rates, resupply_qts_required, alert_summary, consumption_profiles, stock_status,\
    lead_times, reporting_rate, user_profiles, hsas, health_facilities


reports_slug_map = {
    'dashboard': dashboard,
    'emergency-orders': emergency_orders,
    'order-fill-rate': order_fill_rates,
    're-supply-qts-required': resupply_qts_required,
    'alert-summary': alert_summary,
    'consumption-profiles': consumption_profiles,
    'stock-status': stock_status,
    'lead-times': lead_times,
    'reporting-rate': reporting_rate,
    'user-profiles': user_profiles,
    'hsas': hsas,
    'health-facilities': health_facilities,
}

@place_in_request()
@datespan_default
def get_report(request, slug=''):
    report = reports_slug_map[slug].View(slug)
    if not report.can_view(request):
        messages.warning(request,
                         "It looks like you don't have permission to access that view. "
                         "You've been redirected home.")
        return home(request)
    try:
        return report.get_response(request)
    except Exception:
        messages.warning(request,
                         "It looks like there's no data for your filters. "
                         "You've been redirected.")
        return home(request)
        
def home(request):
    try:
        report = reports_slug_map["dashboard"].View("dashboard")
        assert report.can_view(request)
        return report.get_response(request)
    except Exception:
        return render_to_response("%s/no-data.html" % settings.REPORT_FOLDER, 
                                  {}, context_instance=RequestContext(request))
    

