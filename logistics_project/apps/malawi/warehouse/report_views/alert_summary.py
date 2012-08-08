from logistics.models import SupplyPoint

from logistics_project.apps.malawi.warehouse.models import Alert
from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.util import get_country_sp, fmt_pct,\
	facility_supply_points_below

class View(warehouse_view.MalawiWarehouseView):

	def get_context(self, request):
		table = {
			"id": "current-alert-summary",
			"is_datatable": True,
			"header": ["Facility", "#HSAs", "%HSAs stocked out",\
			"%HSAs with EOs that HCs cannot resupply", "%HSAs resupplied but remain below EO",\
			"%HSAs registered but not added products managed", "%HSAs reporting receipts"],
			"data": [],
		}

		sp = SupplyPoint.objects.get(location=request.location)\
			if request.location else get_country_sp()

		facilities = facility_supply_points_below(sp.location)

		for fac in facilities:
			alerts = Alert.objects.get(supply_point=fac)
			table["data"].append([fac.name, alerts.num_hsas,\
				fmt_pct(alerts.have_stockouts, alerts.total_requests),\
				fmt_pct(alerts.eo_without_resupply, alerts.eo_total),\
				fmt_pct(alerts.eo_with_resupply, alerts.eo_total),\
				fmt_pct(alerts.without_products_managed, alerts.num_hsas),\
				fmt_pct((alerts.order_readys - alerts.reporting_receipts), alerts.order_readys)])

		return {"table": table}
