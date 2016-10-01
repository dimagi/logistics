from django.utils.datastructures import SortedDict
from logistics.models import SupplyPoint
from logistics_project.apps.malawi.util import pct, fmt_pct, get_default_supply_point, remove_test_district
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityDataSummary,\
    Alert
from logistics_project.apps.malawi.warehouse.report_utils import current_report_period, \
    get_multiple_reporting_rates_chart, supply_point_type_display
from logistics_project.apps.malawi.warehouse import warehouse_view
from django.core.exceptions import ObjectDoesNotExist

class View(warehouse_view.DashboardView):

    def custom_context(self, request):
        window_date = current_report_period()
        sp = SupplyPoint.objects.get(location=request.location)\
            if request.location else get_default_supply_point(request.user)

        # reporting rates + stockout summary
        child_sps = SupplyPoint.objects.filter(active=True, supplied_by=sp)

        # filter 'test district' out for non-superusers
        if not request.user.is_superuser:
            child_sps = remove_test_district(child_sps)

        child_sp_type = "Location" if not child_sps \
            else supply_point_type_display(child_sps[0].type)

        summary_data = SortedDict()
        avail_sums = ProductAvailabilityDataSummary.objects.filter(supply_point__in=child_sps, 
                                                                   date=window_date)
        for avail_sum in avail_sums:
            stockout_pct = pct(avail_sum.any_without_stock,
                               avail_sum.any_managed) 
            summary_data[avail_sum.supply_point] = {"stockout_pct": stockout_pct}
        
        dsummary_table = {
            "id": "reporting-rates-and-stockout-summary",
            "is_datatable": False,
            "is_downloadable": False,
            "header": [child_sp_type, "% HSA with at least one stockout"],
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
            alert_table["data"].append(["With any pending orders",\
                fmt_pct(alerts.products_requested, alerts.total_requests)])
            alert_table["data"].append(["With any pending approved orders",\
                fmt_pct(alerts.products_approved, alerts.total_requests)])



        except ObjectDoesNotExist:
            pass
        
        return {
            "window_date": window_date,
            "dsummary_table": dsummary_table,
            "alert_table": alert_table,
            "graphdata": get_multiple_reporting_rates_chart(
                child_sps,
                window_date,
                base_level=request.base_level
            ),
        }
