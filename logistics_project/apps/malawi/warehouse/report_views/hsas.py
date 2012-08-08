from logistics.models import SupplyPoint, Product

from logistics_project.apps.malawi.warehouse.models import UserProfileData,\
    ProductAvailabilityDataSummary, ProductAvailabilityData
from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.util import get_country_sp, fmt_pct,\
    hsa_supply_points_below

class View(warehouse_view.MalawiWarehouseView):

    def custom_context(self, request):

        if request.GET.get('hsa_code'):
            self.slug = 'single_hsa'
            return self.single_hsa_context(request)
        
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

    def single_hsa_context(self, request):
        table = {
            "id": "hsa-reporting-summary",
            "is_datatable": False,
            "header": ["Months", "On Time", "Late", "Complete"],
            "data": [['Jan', 22, 42, 53], ['Feb', 22, 25, 41], ['Mar', 41, 41, 46]],
        }

        table2 = {
            "id": "calc-consumption-stock-levels",
            "is_datatable": False,
            "header": ["Product", "Total Calc Cons", "Avg Rep Rate", "AMC", "Total SOH", "Avg MOS",
                "Avg Days Stocked Out", "Total Adj Calc Cons", "Resupply Qts Required"],
            "data": [['CC', 33, 42, 53, 23, 0, 2, 4, 2]],
        }

        table3 = {
            "id": "order-response-time",
            "is_datatable": False,
            "header": ["Product", "Is Emergency", "Balance", "Amt Requested", "Amt Received", "Requested On",
                "Responded On", "Received On", "Status"],
            "data": [['CC', 33, 42, 53, 23, 0, 2, 4, 2]],
        }

        table4 = {
            "id": "recent-messages",
            "is_datatable": False,
            "header": ["Date", "Message Text"],
            "data": [['2012-05-04', 'soh cc 12']],
        }

        table5 = {
            "id": "hsa-details",
            "is_datatable": False,
            "header": ["", ""],
            "data": [['District', 'BULA']],
        }


        return {"table": table,
                "table2": table2,
                "table3": table3,
                "table4": table4,
                "table5": table5,
        }

def _get_hsa_url(hsa):
    return '/malawi/r/hsas/?hsa_code=%s' % hsa.code

def _yes_or_no(number):
    if number > 0:
        return 'yes'
    return 'no'
