from django.conf import settings
from django.utils.datastructures import SortedDict

from logistics.models import Product, SupplyPoint
from logistics.warehouse_view import WarehouseView

from logistics_project.apps.malawi.util import get_facilities, get_districts,\
    get_country_sp
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData, ReportingRate
from logistics_project.apps.malawi.warehouse.report_utils import malawi_default_date_func,\
    current_report_period, pct


class MalawiWarehouseView(WarehouseView):

    def shared_context(self, request):
        base_context = super(MalawiWarehouseView, self).shared_context(request)

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

        base_context.update({ 
            "default_chart_width": 530 if settings.STYLE=='both' else 730,
            "districts": get_districts(),
            "facilities": get_facilities(),
            "hsas": SupplyPoint.objects.filter(active=True, type__code="hsa").count(),
            "reporting_rate": current_rr.pct_reported,
            "products": products,
            "product_stockout_pcts": stockout_pcts,
            "location": request.location or country.location,
            "nav_mode": "direct-param",
        })
        return base_context

    def get_context(self, request):
        pass