from datetime import datetime

from django.utils.datastructures import SortedDict

from dimagi.utils.dates import months_between

from logistics.models import Product

from logistics_project.apps.malawi.util import get_country_sp
from logistics_project.apps.malawi.warehouse.models import OrderRequest
from logistics_project.apps.malawi.warehouse.report_utils import get_reporting_rates_chart,\
    current_report_period, get_window_date, get_window_range, pct, increment_dict_item
from logistics_project.apps.malawi.warehouse import warehouse_view


class View(warehouse_view.MalawiWarehouseView):

    def get_context(self, request):
        sp_code = request.GET.get('place') or get_country_sp().code
        window_range = get_window_range(request)

        oreqs = OrderRequest.objects.filter(supply_point__code=sp_code, date__range=window_range)
        prd_map = SortedDict()
        type_map = SortedDict()
        for product in Product.objects.all():
            prd_map[product] = {}
            type_map[product.type] = {}

        max_val = 0
        for oreq in oreqs:
            prd_map[oreq.product]['emergency'] = increment_dict_item(prd_map[oreq.product], 'emergency', oreq.emergency)
            prd_map[oreq.product]['total'] = increment_dict_item(prd_map[oreq.product], 'total', oreq.total)
            prd_map[oreq.product]['pct'] = pct(prd_map[oreq.product]['emergency'],prd_map[oreq.product]['total'])
            type_map[oreq.product.type]['emergency'] = increment_dict_item(prd_map[oreq.product.type], 'emergency', oreq.emergency)
            type_map[oreq.product.type]['total'] = increment_dict_item(prd_map[oreq.product.type], 'total', oreq.total)
            type_map[oreq.product.type]['pct'] = pct(prd_map[oreq.product.type]['emergency'],prd_map[oreq.product.type]['total'])
            max_val = 100

        # fake test data delete this ######
        from random import random
        prd_map = SortedDict()
        type_map = SortedDict()
        for product in Product.objects.all():
            prd_map[product] = {}
            prd_map[product]['emergency'] = random()*50
            prd_map[product]['total'] = prd_map[product]['emergency']*(random()+1)
            prd_map[product]['pct'] = pct(prd_map[product]['emergency'], prd_map[product]['total'])
            type_map[product.type] = {}
            type_map[product.type]['emergency'] = random()*50
            type_map[product.type]['total'] = type_map[product.type]['emergency']*(random()+1)
            type_map[product.type]['pct'] = pct(type_map[product.type]['emergency'], type_map[product.type]['total'])
            max_val = 100
        # end test data ####### 

        # prd_map = remove_zeros_from_dict(prd_map, 'total')[0]
        # type_map = remove_zeros_from_dict(type_map, 'total')[0]

        summary = {
            "number": 0,
            "xlabels": [],
            "legenddiv": "legend-div",
            "div": "chart-div",
            "max_value": max_val,
            "width": "100%",
            "height": "200px",
            "data": [],
            "xaxistitle": "Products",
            "yaxistitle": "Orders"
        }
        
        # for label in ['pct']:
        for label in ['emergency', 'total']:
            summary["number"] += 1

            product_codes = []
            count = 0

            data_map = {}
            data_map[label] = []
            
            for eo in prd_map.keys():
                count += 1
                product_codes.append([count, '<span>%s</span>' % (str(eo.code.lower()))])
                if prd_map[eo].has_key(label):
                    data_map[label].append([count, prd_map[eo][label]])
            
            summary['data'].append({"label": label, "data": data_map[label]})

        summary['xlabels'] = product_codes

        table = {
            "title": "%HSA with Emergency Order by Product",
            "cell_width": "135px",
            "header": ["Product"],
            "data": []
        }

        line_chart = {
            "height": "350px",
            "width": "100%", # "300px",
            "series": [],
        }

        line_data = []
        for year, month in months_between(request.datespan.startdate, request.datespan.enddate):
            table["header"].append(datetime(year,month,1).strftime("%b-%Y"))
            for eo in prd_map.keys():
                table["data"].append([eo.sms_code, prd_map[eo]['pct']])
            for type in type_map.keys():
                line_data.append([datetime(year, month, 1).strftime("%b-%Y"), type_map[type]['pct']])

        for type in type_map.keys():
            line_chart["series"].append({"title": type.name, "data": line_data})

        return {
                'summary': summary,
                'table': table,
                'line': line_chart
                }
