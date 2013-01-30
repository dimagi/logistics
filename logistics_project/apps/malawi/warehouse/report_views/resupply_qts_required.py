from django.db.models import Q

from logistics.util import config
from logistics.models import StockRequest, Product, SupplyPoint

from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.util import get_default_supply_point,\
    facility_supply_points_below, is_district, is_country, is_facility,\
    hsa_supply_points_below
from collections import defaultdict

class View(warehouse_view.DistrictOnlyView):

    def custom_context(self, request):
        
        table = {
            "id": "quantity-required-for-resupply",
            "is_datatable" : True,
            "is_downloadable": True,
            "header": [],
            "data": [],
        }

        emergency = True
        selected_type = "yes"
        if request.GET.get("emergency"):
            selected_type = str(request.GET.get("emergency"))
            emergency = selected_type == "yes"

        sp = SupplyPoint.objects.get(location=request.location)\
            if request.location else get_default_supply_point(request.user)
        
        if is_country(sp):
            table["header"] = ["District Name"]
            facilities = SupplyPoint.objects.filter(type__code=config.SupplyPointCodes.DISTRICT)
        elif is_district(sp):
            table["header"] = ["Facility Name"]
            facilities = facility_supply_points_below(sp.location)
        else:
            assert is_facility(sp)
            table["header"] = ["HSA Name"]
            facilities = hsa_supply_points_below(sp.location)

        products = Product.objects.order_by('sms_code')
        for product in products:
            table["header"].append(product.name)

        totals = defaultdict(lambda: 0)
        for fac in facilities:
            temp = [fac.name]
            for product in Product.objects.all().order_by('sms_code'):
                temp.append(sum([r.amount_requested for r in StockRequest.pending_requests()\
                    .filter(Q(supply_point=fac) | Q(supply_point__supplied_by=fac)\
                        | Q(supply_point__supplied_by__supplied_by=fac))\
                    .filter(product=product, is_emergency=emergency)]))
                totals[product] += temp[-1]
            table["data"].append(temp)

        # include totals row
        table['data'].append(["Totals"] + [totals[p] for p in products])
        table["height"] = min(480, (facilities.count()+1)*30)
        return {
            "table": table,
            "selected_type": selected_type
        }
