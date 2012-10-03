import json
from collections import defaultdict

from logistics.models import Product, SupplyPoint, ProductType, ProductStock

from logistics_project.apps.malawi.util import get_default_supply_point, fmt_pct, pct
from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.warehouse.report_utils import get_datelist,\
    get_stock_status_table_data, previous_report_period
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData
from django.db.models.aggregates import Sum
from django.shortcuts import get_object_or_404

class View(warehouse_view.DistrictOnlyView):

    def custom_context(self, request):        
        typecode = request.GET.get("product-type")
        selected_type = get_object_or_404(ProductType, code=typecode) \
            if typecode else ProductType.objects.all()[0]
        
        pcode = request.GET.get("product")
        selected_product = get_object_or_404(Product, sms_code=pcode) \
            if pcode else Product.objects.all()[0]
        
        
        sp = SupplyPoint.objects.get(location=request.location) \
            if request.location else get_default_supply_point(request.user)
        
        headings = ["% HSA Stocked Out", "% HSA Under", "% HSA Adequate", 
                    "% HSA Overstocked", "% HSA Not Reported"]
        ordered_slugs = ["without_stock", "under_stock", 
                         "good_stock", "over_stock",
                         "without_data"]
        
        # data by product
        new_headings = ["Product", "Average Monthly Consumption (last 60 days)",
                        "TOTAL SOH (day of report)", "MOS (current period)",
                        "Stock Status"]
        status_data = get_stock_status_table_data(sp)
        status_table = {
            "id": "product-table",
            "is_datatable": False,
            "is_downloadable": True,
            "header": new_headings,
            "data": status_data,
        }
        
        district_table = {
            "id": "district-table",
            "is_datatable": False,
            "is_downloadable": True,
            "header": ["District"] + headings,
            "data": [],
        }
        

        facility_table = {
            "id": "facility-table",
            "is_datatable": True,
            "is_downloadable": True,
            "header": ["Facility"] + headings,
            "data": [],
        }


        hsa_table = {
            "id": "hsa-months-of-stock",
            "is_datatable": True,
            "is_downloadable": True,
            "header": ["HSA"],
            "data": [],
        }

                
        def _get_product_status_table(supply_points, products):
            ret = []
            for s in supply_points:
                qs = ProductAvailabilityData.objects.filter(supply_point=s, 
                                                            product__in=products)
                values = qs.aggregate(Sum('managed_and_without_stock'),
                                      Sum('managed_and_under_stock'),
                                      Sum('managed_and_good_stock'),
                                      Sum('managed_and_over_stock'),
                                      Sum('managed_and_without_data'),
                                      Sum('managed'))
                ret.append([s.name] + \
                           [fmt_pct(values["managed_and_%s__sum" % k], 
                                    values["managed__sum"]) \
                            for k in ordered_slugs])
            return ret
            
        if self._context["national_view_level"]:
            district_table["data"] = _get_product_status_table\
                (SupplyPoint.objects.filter(location__in=self._context['districts']), 
                 [selected_product])
            
            
            
        else:
            facility_table["data"] = _get_product_status_table\
                (SupplyPoint.objects.filter(location__in=self._context['facilities']), 
                 [selected_product])

            for product in Product.objects.all().order_by('sms_code'):
                hsa_table["header"].append(product.sms_code)

            # this chart takes a long time to load
            for hsa in SupplyPoint.objects.filter(location__in=self._context["visible_hsas"]):
                temp = [hsa.name]
                for product in Product.objects.all().order_by('sms_code'):
                    ps = ProductStock.objects.filter(supply_point=hsa, product=product)
                    if ps.count():
                        mr = ps[0].months_remaining
                        if mr:
                            temp.append('%.1f' % mr)
                        else:
                            temp.append('-')
                    else:
                        temp.append('-')
                hsa_table["data"].append(temp)
        
        data = defaultdict(lambda: defaultdict(lambda: 0)) 
        dates = get_datelist(request.datespan.startdate, 
                             request.datespan.enddate)
        
        # product line chart 
        products = Product.objects.filter(type=selected_type) 
        for p in products:
            for dt in dates:
                pad = ProductAvailabilityData.objects.get\
                    (supply_point=sp, product=p, date=dt)
                data[p][dt] = pct(pad.managed_and_without_stock, pad.managed)
        
        graph_data = [{'data': [[i + 1, data[p][dt]] for i, dt in enumerate(dates)],
                       'label': p.sms_code, 'lines': {"show": True}, 
                       "bars": {"show": False}} \
                       for p in products]
        graph_chart = {
            "div": "product-stockouts-chart",
            "legenddiv": "product-stockouts-chart-legend",
            "legendcols": 10,
            "max_value": 100,
            "yaxistitle": "% SO",
            "height": "350px",
            "width": "100%", # "300px",
            "xlabels": [[i + 1, '%s' % dt.strftime("%b")] for i, dt in enumerate(dates)],
            "data": json.dumps(graph_data),
        }

        return {
            'product_types': ProductType.objects.all(),
            'window_date': previous_report_period(),
            'selected_type': selected_type,
            'selected_product': selected_product,
            'status_table': status_table,
            'district_table': district_table,
            'facility_table': facility_table,
            'hsa_table': hsa_table,
            'graphdata': graph_chart,
        }


