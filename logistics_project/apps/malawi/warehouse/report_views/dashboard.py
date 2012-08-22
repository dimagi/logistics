from django.conf import settings
from django.utils.datastructures import SortedDict

from logistics.models import SupplyPoint

from logistics_project.apps.malawi.util import get_districts, pct, fmt_pct,\
    get_default_supply_point
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityDataSummary,\
    ReportingRate, Alert
from logistics_project.apps.malawi.warehouse.report_utils import get_reporting_rates_chart,\
    current_report_period, get_window_date
from logistics_project.apps.malawi.warehouse import warehouse_view
from django.core.exceptions import ObjectDoesNotExist


class View(warehouse_view.DashboardView):

    def custom_context(self, request):
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
            "is_downloadable": False,
            "header": ["District", "Rep Rate", "% HSA with at least one stockout"],
            "data": [],
        }
        for d, vals in summary_data.iteritems():
            dsummary_table["data"].append([d.name, "%.1f%%" % vals["reporting_rate"], "%.1f%%" % vals["stockout_pct"]])


        alert_table = {
            "id": "alert-table",
            "is_datatable": False,
            "is_downloadable": False,
            "header": ["", "% HSAs"],
            "data": [],
        }
        
        sp = SupplyPoint.objects.get(location=request.location)\
            if request.location else get_default_supply_point(request.user)

        try:
            alerts = Alert.objects.get(supply_point=sp)
            alert_table["data"].append(["With EOs that HCs cannot resupply",\
                fmt_pct(alerts.eo_without_resupply, alerts.eo_total)])
            alert_table["data"].append(["Resupplied but remain below EO",\
                fmt_pct(alerts.eo_with_resupply, alerts.eo_total)])

        except ObjectDoesNotExist:
            pass
        
        # report chart
        return {"dsummary_table": dsummary_table,
                "alert_table": alert_table,
                "graphdata": get_reporting_rates_chart(request.location, 
                                                       request.datespan.startdate, 
                                                       window_date)}