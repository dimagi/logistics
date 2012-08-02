from datetime import datetime

from django.utils.datastructures import SortedDict

from dimagi.utils.dates import months_between

from logistics.models import Product

from logistics_project.apps.malawi.util import get_country_sp
from logistics_project.apps.malawi.warehouse.models import OrderFulfillment
from logistics_project.apps.malawi.warehouse.report_utils import get_reporting_rates_chart,\
    current_report_period, get_window_date, get_window_range, pct, increment_dict_item
from logistics_project.apps.malawi.warehouse import warehouse_view


class View(warehouse_view.MalawiWarehouseView):

    def get_context(self, request):
        sp_code = request.GET.get('place') or get_country_sp().code
        window_range = get_window_range(request)

        order_data = OrderFulfillment.objects.filter(supply_point__code=sp_code, date__range=window_range)

        line_chart = {
            "height": "350px",
            "width": "100%", # "300px",
            "series": [],
        }

        prd_map = SortedDict()
        type_map = SortedDict()
        for product in Product.objects.all():
            prd_map[product] = {}
            type_map[product.type] = {}

        for oreq in order_data:
            prd_map[oreq.product]['requested'] = increment_dict_item(prd_map[oreq.product], 'requested', oreq.quantity_requested)
            prd_map[oreq.product]['received'] = increment_dict_item(prd_map[oreq.product], 'received', oreq.quantity_received)
            prd_map[oreq.product]['pct'] = pct(prd_map[oreq.product]['requested'],prd_map[oreq.product]['received'])
            type_map[oreq.product.type]['requested'] = increment_dict_item(prd_map[oreq.product.type], 'requested', oreq.quantity_requested)
            type_map[oreq.product.type]['received'] = increment_dict_item(prd_map[oreq.product.type], 'received', oreq.quantity_received)
            type_map[oreq.product.type]['pct'] = pct(prd_map[oreq.product.type]['received'],prd_map[oreq.product.type]['requested'])

        for label in ['requested', 'received']:
            pass        

        for type in type_map.keys():
            if type_map[type].has_key('pct'):
                val = type_map[type]['pct']
            else:
                val = 0
            line_chart["series"].append({"title": type, "data": [type.id, val]})


        table1 = {
            "title": "Monthly Average OFR by Product (%)",
            "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
            "data": [['cc', 32, 41, 54, 35], ['dt', 23, 22, 41, 16], ['sr', 45, 44, 74, 26]],
            "cell_width": "135px",
        }

        table2 = {
            "title": "OFR for Selected Time Period by Facility and Product (%)",
            "header": ["Facility", "bi", "cl", "cf", "cm"],
            "data": [[3, 3, 4, 5, 3], [2, 2, 2, 4, 1], [4, 4, 4, 4, 6]],
            "cell_width": "135px",
        }


        return {
                'table1': table1,
                'table2': table2,
                'line': line_chart
                }