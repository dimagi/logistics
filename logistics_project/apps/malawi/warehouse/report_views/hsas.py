from logistics.models import SupplyPoint

from logistics_project.apps.malawi.warehouse.models import UserProfileData,\
    ProductAvailabilityDataSummary
from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.util import get_country_sp, fmt_pct,\
    hsa_supply_points_below

class View(warehouse_view.MalawiWarehouseView):

    def get_context(self, request):
        table = {
            "id": "all-hsas",
            "is_datatable": True,
            "header": ["Facility", "Name", "Id", "Responsible for these Commodities",\
                "Products Stocked Out","Products Below Emergency","Products in Adequate Supply",\
                "Products Over Stocked", "Last Message Date"],
            "data": [],
        }

        sp = SupplyPoint.objects.get(location=request.location)\
            if request.location else get_country_sp()

        hsas = hsa_supply_points_below(sp.location)

        for hsa in hsas:
            up = UserProfileData.objects.get(supply_point=hsa)
            pads = ProductAvailabilityDataSummary.objects.filter(supply_point=hsa).order_by('-date')[0]
            table["data"].append({"url": _get_hsa_url(hsa), "data": [hsa.supplied_by.name, hsa.name,\
                hsa.code, up.products_managed, pads.any_without_stock, pads.any_emergency_stock,\
                pads.any_good_stock, pads.any_over_stock,\
                up.last_message.date.strftime("%Y-%m-%d %H:%M:%S")]})

        return {
                "table": table,
        }

def _get_hsa_url(hsa):
    return '/malawi/r/hsa/%s' % hsa.code
