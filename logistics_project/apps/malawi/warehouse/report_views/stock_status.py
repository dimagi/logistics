import json
from collections import defaultdict

from logistics.models import Product, SupplyPoint, ProductType, ProductStock

from logistics_project.apps.malawi.util import get_default_supply_point, fmt_pct, pct
from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.warehouse.report_utils import get_datelist
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData,\
    ProductAvailabilityDataSummary

class View(warehouse_view.DistrictOnlyView):

    def custom_context(self, request):        
        selected_type = None
        if request.GET.get("product-type") in [ptype.code for ptype in ProductType.objects.all()]:
            selected_type = ProductType.objects.get(code=request.GET["product-type"])
        
        sp = SupplyPoint.objects.get(location=request.location) \
            if request.location else get_default_supply_point(request.user)
        
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

        product_table = {
            "id": "product-table",
            "is_datatable": False,
            "header": ["Product"] + headings,
            "data": product_data,
        }
        
        district_table = {
            "id": "district-table",
            "is_datatable": False,
            "header": ["District"] + headings,
            "data": [],
        }
        

        facility_table = {
            "id": "facility-table",
            "is_datatable": True,
            "header": ["Facility"] + headings,
            "data": [],
        }


        hsa_table = {
            "id": "hsa-months-of-stock",
            "is_datatable": True,
            "header": ["HSA"],
            "data": [],
        }

        if self._context["national_view_level"]:
            d_pads_tuples = [(d, ProductAvailabilityDataSummary.objects.get\
                              (supply_point=d, date=date)) \
                            for d in SupplyPoint.objects.filter(location__in=self._context['districts'])]

            
            district_table["data"] = [[d.name] + \
                            [fmt_pct(getattr(pads, "any_%s" % k), pads.any_managed) \
                             for k in ordered_slugs] \
                            for d, pads in d_pads_tuples]

        else:
            f_pads_tuples = [(d, ProductAvailabilityDataSummary.objects.get\
                              (supply_point=d, date=date)) \
                            for d in SupplyPoint.objects.filter(location__in=self._context['facilities'])]

            
            facility_table["data"] = [[d.name] + \
                            [fmt_pct(getattr(pads, "any_%s" % k), pads.any_managed) \
                             for k in ordered_slugs] \
                            for d, pads in f_pads_tuples]


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
        
        # product line chart 
        products = Product.objects.filter(type=selected_type) if selected_type else \
            Product.objects.all()
        data = defaultdict(lambda: defaultdict(lambda: 0)) 
        dates = get_datelist(request.datespan.startdate, 
                             request.datespan.enddate)

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
            "height": "350px",
            "width": "100%", # "300px",
            "xlabels": [[i + 1, '%s' % dt.strftime("%b")] for i, dt in enumerate(dates)],
            "data": json.dumps(graph_data),
        }

        return {
            'product_types': ProductType.objects.all(),
            'selected_type': selected_type,
            'product_table': product_table,
            'district_table': district_table,
            'facility_table': facility_table,
            'hsa_table': hsa_table,
            'graphdata': graph_chart,
        }


