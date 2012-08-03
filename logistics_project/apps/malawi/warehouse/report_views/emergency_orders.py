import itertools
from datetime import datetime

from django.utils.datastructures import SortedDict

from dimagi.utils.dates import months_between

from logistics.models import Product

from logistics_project.apps.malawi.util import get_country_sp, pct
from logistics_project.apps.malawi.warehouse.models import OrderRequest
from logistics_project.apps.malawi.warehouse.report_utils import get_reporting_rates_chart,\
    current_report_period, get_window_date, get_window_range, increment_dict_item,\
    get_datelist, avg_of_key_values, list_key_values
from logistics_project.apps.malawi.warehouse import warehouse_view


class View(warehouse_view.MalawiWarehouseView):

    def get_context(self, request):
        sp_code = request.GET.get('place') or get_country_sp().code

        oreqs = {}
        for date in get_datelist(request.datespan.startdate, request.datespan.enddate):
            oreqs[date.strftime('%Y-%m')] =\
                OrderRequest.objects.filter(supply_point__code=sp_code, date=date)
        prd_map = SortedDict()
        type_map = SortedDict()
        for product in Product.objects.all():
            prd_map[product] = {}
            type_map[product.type] = {}
            for label in ['emergency', 'total', 'pct']:
                prd_map[product][label] = {}
                type_map[product.type][label] = {}

        max_val = 0
        for key in oreqs.keys():
            for oreq in oreqs[key]:
                prd_map[oreq.product]['emergency'][key] = increment_dict_item(prd_map[oreq.product], 'emergency', oreq.emergency)
                prd_map[oreq.product]['total'][key] = increment_dict_item(prd_map[oreq.product], 'total', oreq.total)
                prd_map[oreq.product]['pct'][key] = pct(prd_map[oreq.product]['emergency'][key],prd_map[oreq.product]['total'][key])
                type_map[oreq.product.type]['emergency'][key] = increment_dict_item(prd_map[oreq.product.type], 'emergency', oreq.emergency)
                type_map[oreq.product.type]['total'][key] = increment_dict_item(prd_map[oreq.product.type], 'total', oreq.total)
                type_map[oreq.product.type]['pct'][key] = pct(prd_map[oreq.product.type]['emergency'][key],prd_map[oreq.product.type]['total'][key])
                max_val = 100


        # prd_map = remove_zeros_from_dict(prd_map, 'total')[0]
        # type_map = remove_zeros_from_dict(type_map, 'total')[0]

        summary = {
            "legendcols": 0,
            "xlabels": [],
            "legenddiv": "legend-div",
            "show_legend": "true",
            "div": "chart-div",
            "max_value": max_val,
            "width": "100%",
            "height": "200px",
            "data": [],
            "xaxistitle": "Products",
            "yaxistitle": "Orders"
        }
        
        include_stacks = ['pct']
        for label in include_stacks:
            if len(include_stacks) < 2:
                summary["show_legend"] = "false"

            summary["legendcols"] += 1

            product_codes = []
            count = 0

            data_map = {}
            data_map[label] = []
            
            for eo in prd_map.keys():
                count += 1
                product_codes.append([count, '<span>%s</span>' % (str(eo.code.lower()))])
                if prd_map[eo].has_key(label):
                    all_months = avg_of_key_values(prd_map[eo][label],\
                            [date.strftime('%Y-%m') for date in\
                                get_datelist(request.datespan.startdate, request.datespan.enddate)])
                    data_map[label].append([count, all_months])
            
            summary['data'].append({"label": label, "data": data_map[label]})

        summary['xlabels'] = product_codes

        eo_table = {
            "id": "hsa-emergency-order-product",
            "is_datatable": True,
            "header": ["Product"],
            "data": []
        }

        line_chart = {
            "height": "350px",
            "width": "100%", # "300px",
            "div": "eo-line-chart",
            "legenddiv": "eo-line-legend",
            "legend-cols": 5,
            "xaxistitle": '',
            "yaxistitle": '',
            "max_value": 100,
            "xlabels": [],
            "data": []
        }

        count = 0
        for date in get_datelist(request.datespan.startdate, request.datespan.enddate):
            count += 1
            line_chart["xlabels"].append([count, date.strftime("%b-%Y")])
            eo_table["header"].append(date.strftime("%b-%Y"))
        for eo in prd_map.keys():
            eo_table["data"].append([item for item in itertools.chain([eo.sms_code], list_key_values(prd_map[eo]['pct']))])
        for type in type_map.keys():
            count = 0
            temp = {'data': [],
                    'label': str(type.name),
                    'lines': {"show": 1},
                    'bars': {"show": 0}
                    }
            for date in get_datelist(request.datespan.startdate, request.datespan.enddate):
                count += 1
                temp["data"].append([count, type_map[type]['pct'][date.strftime('%Y-%m')]])
            line_chart["data"].append(temp)

        return {
                'summary': summary,
                'eo_table': eo_table,
                'line': line_chart
                }
