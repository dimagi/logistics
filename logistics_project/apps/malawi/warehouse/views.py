from django.conf import settings
from django.template.context import RequestContext
from django.shortcuts import render_to_response
from django.contrib import messages

from logistics.decorators import place_in_request

from logistics_project.apps.malawi.warehouse.report_utils import datespan_default,\
    table_to_csv

from logistics_project.apps.malawi.warehouse.report_views import dashboard, emergency_orders,\
    order_fill_rates, resupply_qts_required, alert_summary, consumption_profiles, stock_status,\
    lead_times, reporting_rate, user_profiles, hsas, health_facilities
from dimagi.utils.parsing import string_to_boolean
import logging


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
        # bit of a hack: for csv expect two these two magic params 
        # and pull the data from the context
        if string_to_boolean(request.GET.get("export_csv", "false")):
            table_id = request.GET.get('table')
            context = report.get_context(request)
            def _find_table(context, table_id):
                for k, v in context.items():
                    if isinstance(v, dict) and v.get('id') == table_id:
                        return v
            table = _find_table(context, table_id)
            if table:
                return table_to_csv(table)
            else:
                messages.error(request, "Sorry, we can't find that table to export.")
        
        return report.get_response(request)
    except Exception, e:
        if settings.DEBUG:
            raise
        logging.exception("problem loading a warehouse view: %s" % e)
        messages.warning(request,
                         "It looks like there's no data for your filters. "
                         "You've been redirected.")
        return home(request)
        
@place_in_request()
@datespan_default
def home(request):
    try:
        report = reports_slug_map["dashboard"].View("dashboard")
        assert report.can_view(request)
        return report.get_response(request)
    except Exception:
        return render_to_response("%s/no-data.html" % settings.REPORT_FOLDER, 
                                  {}, context_instance=RequestContext(request))
    
