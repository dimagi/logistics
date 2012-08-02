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

class WarehouseView(object):

    def __init__(self, request, slug):
        self.context = self.shared_context(request)
        self.context.update(self.get_context(request))

    def shared_context(self, request):
        to_stub = lambda x: {"name": x, "slug": REPORT_LIST[x]}
        stub_reports = [to_stub(r) for r in REPORT_LIST.keys()]

        country = get_country_sp()
        products = Product.objects.all().order_by('sms_code')
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
            "report_list": stub_reports,
            "districts": get_districts(),
            "facilities": get_facilities(),
            "hsas": SupplyPoint.objects.filter(active=True, type__code="hsa").count(),
            "reporting_rate": current_rr.pct_reported,
            "products": products,
            "product_stockout_pcts": stockout_pcts,
            "settings": settings,
            "location": request.location or country.location,
            "nav_mode": "direct-param",
        }

    def get_context(self, request):
        pass