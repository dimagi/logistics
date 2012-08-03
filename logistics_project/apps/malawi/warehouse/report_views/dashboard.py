from django.conf import settings
from django.utils.datastructures import SortedDict

from logistics_project.apps.malawi.util import get_districts, pct
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityDataSummary,\
    ReportingRate
from logistics_project.apps.malawi.warehouse.report_utils import get_reporting_rates_chart,\
    current_report_period, get_window_date
from logistics_project.apps.malawi.warehouse import warehouse_view


class View(warehouse_view.MalawiWarehouseView):

    def get_context(self, request):
        window_date = get_window_date(request)

        # reporting rates + stockout summary
        districts = get_districts().order_by('name')
        summary_data = SortedDict()
        for d in districts:
            avail_sum = ProductAvailabilityDataSummary.objects.get(supply_point=d, date=window_date)
            stockout_pct = pct(avail_sum.any_without_stock,
                               avail_sum.any_managed) 
            rr = ReportingRate.objects.get(supply_point=d, date=window_date)
            reporting_rate = pct(rr.reported, rr.total)
            summary_data[d] = {"stockout_pct": stockout_pct,
                               "reporting_rate": reporting_rate}
        
        dsummary_table = {
            "id": "reporting-rates-and-stockout-summary",
            "is_datatable": False,
            "header": ["District", "Rep Rate", "% HSA with at least one stockout"],
            "data": [],
        }
        for d, vals in summary_data.iteritems():
            dsummary_table["data"].append([d.name, "%.1f%%" % vals["reporting_rate"], "%.1f%%" % vals["stockout_pct"]])


        alert_table = {
            "id": "alert-table",
            "is_datatable": False,
            "header": ["", "% HSAs"],
            "data": [],
        }
        # for alert in alerts:
        #     alert_table["data"].append(alert.text, alert.value)


        # report chart
        return {"dsummary_table": dsummary_table,
                "alert_table": alert_table,
                "graphdata": get_reporting_rates_chart(request.location, 
                                                       request.datespan.startdate, 
                                                       window_date)}