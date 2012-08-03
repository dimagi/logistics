from random import random
from datetime import datetime
from collections import defaultdict

from logistics_project.apps.malawi.util import get_country_sp, fmt_pct,\
    get_district_supply_points, pct
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData,\
    ProductAvailabilityDataSummary

from logistics.models import Product, SupplyPoint, ProductType

from logistics_project.apps.malawi.warehouse import warehouse_view
from dimagi.utils.dates import months_between
import json

class View(warehouse_view.MalawiWarehouseView):

    def get_context(self, request):
        ret_obj = {
            'product_types': ProductType.objects.all()
        }
        selected_type = ProductType.objects.get(code=request.GET["product-type"]) \
            if "product-type" in request.GET else None
        
        ret_obj['selected_type'] = selected_type
        
        sp = SupplyPoint.objects.get(location=request.location) \
            if request.location else get_country_sp()
        
        # Correct
        # date = current_report_period()
        date = request.datespan.enddate # testing
        headings = ["% HSA Stocked Out", "% HSA Under", "% HSA Adequate", 
                    "% HSA Overstocked", "% HSA Not Reported"]
        ordered_slugs = ["without_stock", "under_stock", 
                         "good_stock", "over_stock",
                         "without_data"]
        
        
        # data by product
        p_pad_tuples = [(p, ProductAvailabilityData.objects.get\
                                (supply_point=sp, date=date, product=p)) \
                        for p in Product.objects.all().order_by('sms_code')]
        product_data = [[p.sms_code] + \
                        [fmt_pct(getattr(pad, "managed_and_%s" % k), pad.managed) \
                         for k in ordered_slugs] \
                        for p, pad in p_pad_tuples]
        
        ret_obj['product_table'] = {
            "id": "product-table",
            "is_datatable": False,
            "header": ["Product"] + headings,
            "data": product_data,
        }
        
        # data by district
        d_pads_tuples = [(d, ProductAvailabilityDataSummary.objects.get\
                          (supply_point=d, date=date)) \
                        for d in get_district_supply_points().order_by('name')]
        
        district_data = [[d.name] + \
                        [fmt_pct(getattr(pads, "any_%s" % k), pads.any_managed) \
                         for k in ordered_slugs] \
                        for d, pads in d_pads_tuples]
        ret_obj['district_table'] = {
            "id": "district-table",
            "is_datatable": False,
            "header": ["District"] + headings,
            "data": district_data,
        }
        
        # product line chart 
        products = Product.objects.filter(type=selected_type) if selected_type else \
            Product.objects.all()
        data = defaultdict(lambda: defaultdict(lambda: 0)) 
        dates = [datetime(year, month, 1) for year, month in \
                    months_between(request.datespan.startdate, 
                                   request.datespan.enddate)]
        for p in products:
            for dt in dates:
                pad = ProductAvailabilityData.objects.get\
                    (supply_point=sp, product=p, date=dt)
                data[p][dt] = pct(pad.managed_and_without_stock, pad.managed)
        
        graph_data = [{'data': [[i + 1, data[p][dt]] for i, dt in enumerate(dates)],
                       'label': p.sms_code, 'lines': {"show": True}, 
                       "bars": {"show": False}} \
                       for p in products]
        ret_obj['graphdata'] = {
            "div": "product-stockouts-chart",
            "legenddiv": "product-stockouts-chart-legend",
            "legendcols": 10,
            "max_value": 100,
            "height": "350px",
            "width": "100%", # "300px",
            "xlabels": [[i + 1, '%s' % dt.strftime("%b")] for i, dt in enumerate(dates)],
            "data": json.dumps(graph_data),
        }
        return ret_obj
