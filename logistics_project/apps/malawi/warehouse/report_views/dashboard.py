from django.conf import settings
from django.utils.datastructures import SortedDict

from logistics_project.apps.malawi.util import get_districts
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityDataSummary,\
    ReportingRate
from logistics_project.apps.malawi.warehouse.report_utils import get_reporting_rates_chart,\
    current_report_period, get_window_date, pct
from logistics_project.apps.malawi.warehouse.report_views import warehouse

class View(warehouse.WarehouseView):

    def get_context(self, request):
        window_date = get_window_date(request)

        # reporting rates + stockout summary
        districts = get_districts().order_by('name')
        summary_data = SortedDict()
        for d in districts:
            avail_sum = ProductAvailabilityDataSummary.objects.get(supply_point=d, date=window_date)
            stockout_pct = pct(avail_sum.with_any_stockout,
                                 avail_sum.manages_anything) 
            rr = ReportingRate.objects.get(supply_point=d, date=window_date)
            reporting_rate = pct(rr.reported, rr.total)
            summary_data[d] = {"stockout_pct": stockout_pct,
                               "reporting_rate": reporting_rate}
        
        # report chart
        return {"summary_data": summary_data,
                "graphdata": get_reporting_rates_chart(request.location, 
                                                       request.datespan.startdate, 
                                                       window_date),
                "pa_width": 530 if settings.STYLE=='both' else 730 }

