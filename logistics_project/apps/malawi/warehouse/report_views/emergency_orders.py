import itertools
from collections import defaultdict

from logistics.models import SupplyPoint, ProductType, Product

from logistics_project.apps.malawi.util import get_default_supply_point, pct, fmt_or_none,\
    is_facility, hsa_supply_points_below
from logistics_project.apps.malawi.warehouse.models import OrderRequest
from logistics_project.apps.malawi.warehouse.report_utils import get_datelist,\
    avg_of_key_values
from logistics_project.apps.malawi.warehouse import warehouse_view
from django.db.models.aggregates import Sum


class View(warehouse_view.DistrictOnlyView):

    def custom_context(self, request):
        selected_type = None
        if request.GET.get("product-type") in [ptype.code for ptype in ProductType.objects.all()]:
            selected_type = ProductType.objects.get(code=request.GET["product-type"])

        sp = SupplyPoint.objects.get(location=request.location) \
            if request.location else get_default_supply_point(request.user)
        
        datelist = get_datelist(request.datespan.startdate, 
                                request.datespan.enddate)
        oreqs = dict([(date, OrderRequest.objects.filter(supply_point=sp, date=date)) \
                      for date in datelist])
        
        date_headers = [date.strftime("%b-%Y") for date in datelist]
        
        # {product: {label: {date: val}}}
        prd_map = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0))) 
        # {product.type: {label: {date: val}}}
        type_map = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0))) 
        for date in oreqs.keys():
            for oreq in oreqs[date]:
                prd_map[oreq.product]['emergency'][date] += oreq.emergency
                prd_map[oreq.product]['total'][date] += oreq.total
                prd_map[oreq.product]['pct'][date] = pct(prd_map[oreq.product]['emergency'][date],
                                                         prd_map[oreq.product]['total'][date])
                type_map[oreq.product.type]['emergency'][date] += oreq.emergency
                type_map[oreq.product.type]['total'][date] += oreq.total
                type_map[oreq.product.type]['pct'][date] = pct(type_map[oreq.product.type]['emergency'][date],
                                                               type_map[oreq.product.type]['total'][date])
        
        # prd_map = remove_zeros_from_dict(prd_map, 'total')[0]
        # type_map = remove_zeros_from_dict(type_map, 'total')[0]

        summary = {
            "legendcols": 0,
            "xlabels": [],
            "legenddiv": "legend-div",
            "show_legend": "true",
            "div": "chart-div",
            "width": "100%",
            "height": "200px",
            "data": [],
            "xaxistitle": "Products",
            "yaxistitle": "Average % of HSAs with EO"
        }
        
        # NOTE: this is weird? should clean up
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
                product_codes.append([count, '%s' % (str(eo.code.lower()))])
                if prd_map[eo].has_key(label):
                    all_months = avg_of_key_values(prd_map[eo][label], datelist)
                            
                    data_map[label].append([count, all_months])
            
            summary['data'].append({"label": label, "data": data_map[label]})

        summary['xlabels'] = product_codes

        eo_pct_table = {
            "id": "eo-pct-table",
            "is_datatable": True,
            "is_downloadable": True,
            "header": ["Product"] + date_headers,
            "data": []
        }

        line_chart = {
            "height": "350px",
            "width": "100%", # "300px",
            "div": "eo-line-chart",
            "legenddiv": "eo-line-legend",
            "legendcols": 10,
            "xaxistitle": '',
            "yaxistitle": '% HSA with EO',
            "xlabels": [],
            "data": []
        }

        count = 0
        for date in datelist:
            count += 1
            line_chart["xlabels"].append([count, date.strftime("%b-%Y")])

        for eo in prd_map.keys():
            eo_pct_table["data"].append([item for item in itertools.chain\
                                     ([eo.sms_code],
                                      [fmt_or_none(val) for val in [prd_map[eo]['pct'][d] for d in datelist]])])
            
        # for type in type_map.keys():
        selected_products = Product.objects.all()
        if selected_type:
            selected_products = Product.objects.filter(type=selected_type)
        for prd in selected_products:
            count = 0
            temp = {'data': [],
                    # 'label': str(type.name),
                    'label': str(prd.sms_code),
                    'lines': {"show": 1},
                    'bars': {"show": 0}
                    }
            for date in datelist:
                count += 1
                # if type_map[type]['pct'].has_key(date):
                #     temp["data"].append([count, type_map[type]['pct'][date]])
                if prd_map[prd]['pct'].has_key(date):
                    temp["data"].append([count, prd_map[prd]['pct'][date]])
                else:
                    temp["data"].append([count, "No Data"])
            line_chart["data"].append(temp)

        # HSA emergency orders table
        hsa_eo_table = None
        if is_facility(sp):
            hsas = hsa_supply_points_below(sp.location)
            data = [[hsa.name] + \
                    [OrderRequest.objects.filter(supply_point=hsa, date=d) \
                        .aggregate(Sum('total'))["total__sum"] \
                     for d in datelist] 
                    for hsa in hsas]
            hsa_eo_table = {
                "id": "hsa-eo-table",
                "is_datatable": True,
                "is_downloadable": True,
                "header": ["HSA"] + date_headers,
                "data": data
            }

        return {
                'product_types': ProductType.objects.all(),
                'selected_type': selected_type,
                'summary': summary,
                'eo_pct_table': eo_pct_table,
                'hsa_eo_table': hsa_eo_table,
                'line': line_chart
                }
