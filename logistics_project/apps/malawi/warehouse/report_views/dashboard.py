from collections import defaultdict
from django.db.models import Count
from django.utils.datastructures import SortedDict
from logistics.models import SupplyPoint
from logistics_project.apps.malawi.models import RefrigeratorMalfunction
from logistics_project.apps.malawi.util import (pct, fmt_pct, get_default_supply_point, remove_test_district,
    filter_district_queryset_for_epi)
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityDataSummary,\
    Alert
from logistics_project.apps.malawi.warehouse.report_utils import current_report_period, \
    get_multiple_reporting_rates_chart, supply_point_type_display
from logistics_project.apps.malawi.warehouse import warehouse_view
from django.core.exceptions import ObjectDoesNotExist
from static.malawi.config import BaseLevel, SupplyPointCodes


class View(warehouse_view.DashboardView):

    def get_alerts_table(self, request, reporting_supply_point):
        if request.base_level_is_hsa:
            alert_table = {
                "id": "alert-table",
                "is_datatable": False,
                "is_downloadable": False,
                "header": ["", "% HSAs"],
                "data": [],
            }

            try:
                alerts = Alert.objects.get(supply_point=reporting_supply_point)
                alert_table["data"].append(["With EOs that HCs cannot resupply",
                    fmt_pct(alerts.eo_without_resupply, alerts.eo_total)])
                alert_table["data"].append(["Resupplied but remain below EO",
                    fmt_pct(alerts.eo_with_resupply, alerts.eo_total)])
                alert_table["data"].append(["With any pending orders",
                    fmt_pct(alerts.products_requested, alerts.total_requests)])
                alert_table["data"].append(["With any pending approved orders",
                    fmt_pct(alerts.products_approved, alerts.total_requests)])
            except ObjectDoesNotExist:
                pass

            return alert_table

        return None

    def get_stockout_rates_table(self, request, child_sps, window_date):
        child_sp_type = "Location" if not child_sps \
            else supply_point_type_display(child_sps[0].type)

        summary_data = SortedDict()
        avail_sums = ProductAvailabilityDataSummary.objects.filter(
            supply_point__in=child_sps,
            date=window_date,
            base_level=request.base_level
        ).order_by('supply_point__name')
        for avail_sum in avail_sums:
            stockout_pct = pct(avail_sum.any_without_stock,
                               avail_sum.any_managed) 
            summary_data[avail_sum.supply_point] = {"stockout_pct": stockout_pct}

        base_level_description = BaseLevel.get_base_level_description(request.base_level)

        table = {
            "id": "stockout-rates",
            "is_datatable": False,
            "is_downloadable": False,
            "header": [child_sp_type, "%% %s with at least one stockout" % base_level_description],
            "data": [],
        }
        for d, vals in summary_data.iteritems():
            table["data"].append([d.name, "%.1f%%" % vals["stockout_pct"]])

        return table

    def get_district_fridge_summary_table(self, request, reporting_supply_point, child_sps):
        if not request.base_level_is_facility:
            return None

        if reporting_supply_point.type.code == SupplyPointCodes.COUNTRY:
            districts = child_sps
        elif reporting_supply_point.type.code == SupplyPointCodes.DISTRICT:
            districts = [reporting_supply_point]
        else:
            raise BaseLevel.InvalidReportingSupplyPointException(reporting_supply_point.code)

        table = {
            "id": "district-fridge-summary",
            "is_datatable": False,
            "is_downloadable": False,
            "header": [
                "District",
                "% HFs with Fridge - No Gas",
                "% HFs with Fridge - Power Failure",
                "% HFs with Fridge - Breakdown",
                "% HFs with Fridge - Other Issue",
            ],
            "data": [],
        }

        for district in districts:
            total_facilities = SupplyPoint.objects.filter(
                active=True,
                supplied_by=district
            ).count()

            malfunction_reasons = RefrigeratorMalfunction.objects.filter(
                supply_point__active=True,
                supply_point__supplied_by=district,
                resolved_on__isnull=True
            ).values('malfunction_reason').annotate(total=Count('malfunction_reason'))

            reason_counts = defaultdict(lambda: 0)

            for record in malfunction_reasons:
                reason_counts[record['malfunction_reason']] = record['total']

            table["data"].append([
                district.name,
                fmt_pct(reason_counts[RefrigeratorMalfunction.REASON_NO_GAS], total_facilities),
                fmt_pct(reason_counts[RefrigeratorMalfunction.REASON_POWER_FAILURE], total_facilities),
                fmt_pct(reason_counts[RefrigeratorMalfunction.REASON_FRIDGE_BREAKDOWN], total_facilities),
                fmt_pct(reason_counts[RefrigeratorMalfunction.REASON_OTHER], total_facilities),
            ])

        return table

    def get_facility_fridge_summary_table(self, request, reporting_supply_point, child_sps):
        if not (
            request.base_level_is_facility and
            reporting_supply_point.type.code == SupplyPointCodes.DISTRICT
        ):
            return None

        table = {
            "id": "facility-fridge-summary",
            "is_datatable": False,
            "is_downloadable": False,
            "header": [
                "Facility",
                "Fridge - No Gas",
                "Fridge - Power Failure",
                "Fridge - Breakdown",
                "Fridge - Other Issue",
            ],
            "data": [],
        }

        malfunctions = RefrigeratorMalfunction.objects.select_related('supply_point').filter(
            supply_point__in=child_sps,
            resolved_on__isnull=True
        ).order_by('supply_point__name')

        malfunctions = list(malfunctions)

        if not malfunctions:
            return None

        for malfunction in malfunctions:
            table["data"].append([
                malfunction.supply_point.name,
                'x' if malfunction.malfunction_reason == RefrigeratorMalfunction.REASON_NO_GAS else '',
                'x' if malfunction.malfunction_reason == RefrigeratorMalfunction.REASON_POWER_FAILURE else '',
                'x' if malfunction.malfunction_reason == RefrigeratorMalfunction.REASON_FRIDGE_BREAKDOWN else '',
                'x' if malfunction.malfunction_reason == RefrigeratorMalfunction.REASON_OTHER else '',
            ])

        return table

    def custom_context(self, request):
        window_date = current_report_period()
        reporting_supply_point = self.get_reporting_supply_point(request)

        # reporting rates + stockout summary
        child_sps = SupplyPoint.objects.filter(active=True).order_by('name')
        if reporting_supply_point.type_id == SupplyPointCodes.COUNTRY:
            child_sps = child_sps.filter(supplied_by__supplied_by=reporting_supply_point)
            if request.base_level_is_facility:
                child_sps = filter_district_queryset_for_epi(child_sps)
        else:
            child_sps = child_sps.filter(supplied_by=reporting_supply_point)

        # filter 'test district' out for non-superusers
        if not request.user.is_superuser:
            child_sps = remove_test_district(child_sps)

        return {
            "window_date": window_date,
            "stockout_rates_table": self.get_stockout_rates_table(request, child_sps, window_date),
            "alert_table": self.get_alerts_table(request, reporting_supply_point),
            "graphdata": get_multiple_reporting_rates_chart(
                child_sps,
                window_date,
                base_level=request.base_level
            ),
            "district_fridge_summary_table": self.get_district_fridge_summary_table(
                request,
                reporting_supply_point,
                child_sps
            ),
            "facility_fridge_summary_table": self.get_facility_fridge_summary_table(
                request,
                reporting_supply_point,
                child_sps
            ),
        }
