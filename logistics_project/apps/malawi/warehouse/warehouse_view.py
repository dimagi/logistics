from django.utils.datastructures import SortedDict

from logistics.models import Product, SupplyPoint
from logistics.warehouse_view import WarehouseView

from logistics_project.apps.malawi.util import get_facilities, get_districts,\
    get_country_sp
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData, ReportingRate
from logistics_project.apps.malawi.warehouse.report_utils import malawi_default_date_func,\
    current_report_period, pct


class MalawiWarehouseView(WarehouseView):

    def __init__(self, request, slug):
        self.context = self.shared_context(request)
        self.context.update(self.malawi_shared_context(request))
        self.context.update(self.get_context(request))

    def malawi_shared_context(self, request):
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
            "districts": get_districts(),
            "facilities": get_facilities(),
            "hsas": SupplyPoint.objects.filter(active=True, type__code="hsa").count(),
            "reporting_rate": current_rr.pct_reported,
            "products": products,
            "product_stockout_pcts": stockout_pcts,
            "location": request.location or country.location,
            "nav_mode": "direct-param",
        }

    def get_context(self, request):
        pass