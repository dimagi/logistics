from random import random
from logistics_project.apps.malawi.util import get_country_sp, fmt_pct
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData

from logistics.models import Product, SupplyPoint

def get_context(request):
    ret_obj = {}
    
    sp = SupplyPoint.objects.get(location=request.location) \
        if request.location else get_country_sp()
    # Correct
    # date = current_report_period()
    # testing
    date = request.datespan.enddate
    headings = ["% HSA Stocked Out", "% HSA Under", "% HSA Adequate", 
                "% HSA Overstocked", "% HSA Not Reported"]
    slugs = ["managed_and_without_stock", "managed_and_under_stock", 
             "managed_and_with_good_stock", "managed_and_over_stock",
             "managed_and_without_data"]
    p_pad_tuples = [(p, ProductAvailabilityData.objects.get\
                            (supply_point=sp, date=date, product=p)) \
                    for p in Product.objects.all().order_by('sms_code')]
    
    product_data = [[p.sms_code] + \
                    [fmt_pct(getattr(pad, k), pad.managed) for k in slugs] \
                    for p, pad in p_pad_tuples]
    
    ret_obj['product_table'] = {
        "title": "",
        "header": ["Product"] + headings,
        "data": product_data,
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