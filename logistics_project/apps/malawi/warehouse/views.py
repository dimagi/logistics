from django.conf import settings
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect
from django.utils.datastructures import SortedDict

from dimagi.utils.decorators.datespan import datespan_in_request

from logistics.decorators import place_in_request
from logistics.models import Product, SupplyPoint

from logistics_project.apps.malawi.util import get_facilities, get_districts,\
    get_country_sp
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData, ReportingRate
from logistics_project.apps.malawi.warehouse.report_utils import malawi_default_date_func,\
    current_report_period, pct
from logistics_project.apps.malawi.warehouse.report_views import dashboard, emergency_orders,\
    order_fill_rates, resupply_qts_required, alert_summary, consumption_profiles, stock_status,\
    lead_times, reporting_rate


def hsas(request):
    context = {}
    return render_to_response('malawi/new/hsas.html', context, context_instance=RequestContext(request))

def user_profiles(request):
    context = {}
    return render_to_response('malawi/new/user-profiles.html', context, context_instance=RequestContext(request))

slug_map = {
    'dashboard': dashboard,
    'emergency-orders': emergency_orders,
    'order-fill-rate': order_fill_rates,
    're-supply-qts-required': resupply_qts_required,
    'alert-summary': alert_summary,
    'consumption-profiles': consumption_profiles,
    'stock-status': stock_status,
    'lead-times': lead_times,
    'reporting-rate': reporting_rate,
}     

datespan_default = datespan_in_request(
    default_function=malawi_default_date_func,
    format_string='%B %Y'
)
    
@place_in_request()
@datespan_default
def get_report(request, slug=''):
    report = slug_map[slug].View(request, slug)
    return render_to_response("malawi/new/%s.html" % slug, 
                              report.context,
                              context_instance=RequestContext(request))

def home(request):
    return redirect("/malawi/r/dashboard/")
