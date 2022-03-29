from __future__ import unicode_literals
from logistics.models import SupplyPoint

from logistics_project.apps.malawi.warehouse.models import Alert
from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.util import get_default_supply_point, fmt_pct,\
    facility_supply_points_below, is_country, get_district_supply_points

class View(warehouse_view.DistrictOnlyView):

    def custom_context(self, request):
        table = {
            "id": "current-alert-summary",
            "is_datatable": True,
            "is_downloadable": True,
            "header": [
                "Facility",
                "#HSAs",
                "%HSAs stocked out",
                "%HSAs with EOs that HCs cannot resupply",
                "%HSAs resupplied but remain below EO",
                "%HSAs registered but not added products managed",
                "%HSAs not reporting receipts",
                "%HSAs with any pending orders",
                "%HSAs with any pending approved orders",
            ],
            "data": [],
        }

        sp = SupplyPoint.objects.get(location=request.location)\
            if request.location else get_default_supply_point(request.user)

        if is_country(sp):
            facilities = get_district_supply_points(request.user.is_superuser)
        else:
            facilities = facility_supply_points_below(sp.location)

        alertset = Alert.objects.filter(supply_point__in=facilities)
        for alerts in alertset:
            table["data"].append([
                alerts.supply_point.name,
                alerts.num_hsas,
                fmt_pct(alerts.have_stockouts, alerts.total_requests),
                fmt_pct(alerts.eo_without_resupply, alerts.eo_total),
                fmt_pct(alerts.eo_with_resupply, alerts.eo_total),
                fmt_pct(alerts.without_products_managed, alerts.num_hsas),
                fmt_pct((alerts.order_readys - alerts.reporting_receipts), alerts.order_readys),
                fmt_pct(alerts.products_requested, alerts.total_requests),
                fmt_pct(alerts.products_approved, alerts.total_requests),
            ])

        table["height"] = min(480, (facilities.count()+1)*30)

        return {"table": table}
