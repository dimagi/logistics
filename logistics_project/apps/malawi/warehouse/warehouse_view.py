from django.conf import settings
from django.utils.datastructures import SortedDict

from logistics.models import Product, SupplyPoint

from logistics_project.apps.malawi.util import get_facilities, get_districts,\
    get_country_sp, pct
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData, ReportingRate
from logistics_project.apps.malawi.warehouse.report_utils import current_report_period
from logistics.permissions import user_can_view
from logistics.reports import ReportView


class MalawiWarehouseView(ReportView):
    
    @property
    def template_name(self):
        return "malawi/new/%s.html" % self.slug
        
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

class DistrictOnlyView(MalawiWarehouseView):
    """
    Reports that are only available to people whose location is set to 
    a district (or higher). The use case is: I should be able to see this
    report for my district, facilities in my district, or nationally, but 
    not for any other district.
    """
    def can_view(self, request):
        if request.user.is_superuser: return True
        else:
            return user_can_view(request.user, request.location, unconfigured_value=True)