'''
New views for the upgraded reports of the system.
'''
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

REPORT_LIST = SortedDict([
    ("Dashboard", "dashboard"),
    ("Reporting Rate", "reporting-rate"),
    ("Stock Status", "stock-status"),
    ("Consumption Profiles", "consumption-profiles"),
    ("Alert Summary", "alert-summary"),
    ("Re-supply Qts Required", "re-supply-qts-required"),
    ("Lead Times", "lead-times"),
    ("Order Fill Rate", "order-fill-rate"),
    ("Emergency Orders", "emergency-orders"),
])

func_map = {
    'dashboard': dashboard.get_context,
    'emergency-orders': emergency_orders.get_context,
    'order-fill-rate': order_fill_rates.get_context,
    're-supply-qts-required': resupply_qts_required.get_context,
    'alert-summary': alert_summary.get_context,
    'consumption-profiles': consumption_profiles.get_context,
    'stock-status': stock_status.get_context,
    'lead-times': lead_times.get_context,
    'reporting-rate': reporting_rate.get_context,
}     

datespan_default = datespan_in_request(
    default_function=malawi_default_date_func,
    format_string='%B %Y'
)
    
@place_in_request()
@datespan_default
def get_report(request, slug=''):
    report = WarehouseView(request, slug)
    return render_to_response("malawi/new/%s.html" % slug, 
                              report.context,
                              context_instance=RequestContext(request))

def home(request):
    return redirect("/malawi/r/dashboard/")

class WarehouseView(object):

    def __init__(self, request, slug):
        self.context = self.shared_context(request)
        
        # TODO: remove common_context and put report-specific data in report view
        self.context.update(self.common_context(request))

        to_stub = lambda x: {"name": x, "slug": REPORT_LIST[x]}
        stub_reports = [to_stub(r) for r in REPORT_LIST.keys()]

        self.context.update({"report_list": stub_reports,
                    "slug": slug})
        self.context.update(self.get_more_context(request, slug))

    def shared_context(self, request):
        country = get_country_sp()
        return { 
            "settings": settings,
            "location": request.location or country.location,
            "nav_mode": "direct-param",
            "default_chart_width": 530 if settings.STYLE=='both' else 730 
        }

    def common_context(self, request):
        products = Product.objects.all().order_by('sms_code')
        country = get_country_sp()
        date = current_report_period()
        
        # national stockout percentages by product
        stockout_pcts = SortedDict()
        for p in products:
            availability = ProductAvailabilityData.objects.get(supply_point=country,
                                                               date=date,
                                                               product=p)
            stockout_pcts[p] = pct(availability.managed_and_without_stock,
                                    availability.managed)
        
        
        current_rr = ReportingRate.objects.get\
            (date=date, supply_point=country)

        return { 
            "districts": get_districts(),
            "facilities": get_facilities(),
            "hsas": SupplyPoint.objects.filter(active=True, type__code="hsa").count(),
            "reporting_rate": current_rr.pct_reported,
            "products": products,
            "product_stockout_pcts": stockout_pcts,
        }

    def get_more_context(self, request, slug=None):
        if slug in func_map:
            return func_map[slug](request)
        else:
            return {}

        context = func_map[slug](request) if slug in func_map else {}
        context["slug"] = slug
        return context 

