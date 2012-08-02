from random import random
from logistics_project.apps.malawi.util import get_country_sp, fmt_pct,\
    get_district_supply_points
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData,\
    ProductAvailabilityDataSummary

from logistics.models import Product, SupplyPoint

from logistics_project.apps.malawi.warehouse import warehouse_view

class View(warehouse_view.MalawiWarehouseView):

    def get_context(self, request):
        ret_obj = {}
        
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
            "title": "",
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
            "title": "",
            "header": ["District"] + headings,
            "data": district_data,
        }
        
        table2 = {
            "title": "HSA Current Stock Status by District",
            "header": ["District"] + headings,
            "data": [['cc', 33, 45, 52, 31], ['dt', 21, 29, 45, 13], ['sr', 43, 42, 42, 61]],
        }
        line_chart = {
            "height": "350px",
            "width": "100%", # "300px",
            "series": [],
        }
        for j in ['LA 1x6', 'LA 2x6']:
            temp = []
            for i in range(0,5):
                temp.append([random(),random()])
            line_chart["series"].append({"title": j, "data": sorted(temp)})

        ret_obj['table2'] = table2
        ret_obj['line'] = line_chart
        return ret_obj
