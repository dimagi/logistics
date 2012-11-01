from django.conf import settings
from django.utils.datastructures import SortedDict

from logistics.models import SupplyPoint

from logistics_project.apps.malawi.util import get_districts, pct, fmt_pct,\
    get_default_supply_point
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityDataSummary,\
    ReportingRate, Alert
from logistics_project.apps.malawi.warehouse.report_utils import get_reporting_rates_chart,\
    current_report_period, get_window_date, previous_report_period,\
    get_multiple_reporting_rates_chart
from logistics_project.apps.malawi.warehouse import warehouse_view
from django.core.exceptions import ObjectDoesNotExist


class View(warehouse_view.DashboardView):

    def custom_context(self, request):
        window_date = current_report_period()
        sp = SupplyPoint.objects.get(location=request.location)\
            if request.location else get_default_supply_point(request.user)

        # reporting rates + stockout summary
        child_sps = SupplyPoint.objects.filter(active=True, supplied_by=sp)
        
        summary_data = SortedDict()
        for csp in child_sps:
            avail_sum = ProductAvailabilityDataSummary.objects.get(supply_point=csp, date=window_date)
            stockout_pct = pct(avail_sum.any_without_stock,
                               avail_sum.any_managed) 
            summary_data[csp] = {"stockout_pct": stockout_pct}
        
        dsummary_table = {
            "id": "reporting-rates-and-stockout-summary",
            "is_datatable": False,
            "is_downloadable": False,
            "header": ["District", "% HSA with at least one stockout"],
            "data": [],
        }
        for d, vals in summary_data.iteritems():
            dsummary_table["data"].append([d.name, "%.1f%%" % vals["stockout_pct"]])


        alert_table = {
            "id": "alert-table",
            "is_datatable": False,
            "is_downloadable": False,
            "header": ["", "% HSAs"],
            "data": [],
        }
        
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
                "graphdata": get_multiple_reporting_rates_chart(child_sps, window_date)}