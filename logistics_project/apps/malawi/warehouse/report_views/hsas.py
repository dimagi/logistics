from logistics.models import SupplyPoint, Product

from logistics_project.apps.malawi.warehouse.models import UserProfileData,\
    ProductAvailabilityDataSummary, ProductAvailabilityData
from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.util import get_country_sp, fmt_pct,\
    hsa_supply_points_below

class View(warehouse_view.MalawiWarehouseView):

    def custom_context(self, request):
        
        table = {
            "id": "all-hsas",
            "is_datatable": True,
            "header": ["Facility", "Name", "Id", "Responsible for these Commodities",\
                "Has Stockouts","Has Emergency Levels","Has Products with good supply",\
                "Has Overstocks", "Last Message Date"],
            "data": [],
        }

        sp = SupplyPoint.objects.get(location=request.location)\
            if request.location else get_country_sp()

        hsas = hsa_supply_points_below(sp.location)

        for hsa in hsas:
            up = UserProfileData.objects.get(supply_point=hsa)
            pads = ProductAvailabilityDataSummary.objects.filter(supply_point=hsa).order_by('-date')[0]
            table["data"].append({"url": _get_hsa_url(hsa), "data": [hsa.supplied_by.name, hsa.name,\
                hsa.code, up.products_managed,\
                _yes_or_no(pads.any_without_stock), _yes_or_no(pads.any_emergency_stock),\
                _yes_or_no(pads.any_good_stock), _yes_or_no(pads.any_over_stock),\
                up.last_message.date.strftime("%Y-%m-%d %H:%M:%S")]})

        return {
                "table": table,
        }

def _get_hsa_url(hsa):
    return '/malawi/r/hsa/%s' % hsa.code

def _yes_or_no(number):
    if number > 0:
        return 'yes'
    return 'no'
