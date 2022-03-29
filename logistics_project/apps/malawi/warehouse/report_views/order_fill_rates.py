from __future__ import unicode_literals
from collections import defaultdict

from logistics.models import Product, SupplyPoint, ProductType

from logistics_project.apps.malawi.util import get_default_supply_point,\
    facility_supply_points_below, fmt_pct, fmt_or_none, is_district, is_facility,\
    hsa_supply_points_below
from logistics_project.apps.malawi.warehouse.models import OrderFulfillment
from logistics_project.apps.malawi.warehouse.report_utils import get_datelist
from logistics_project.apps.malawi.warehouse import warehouse_view
import json
from django.db.models import Sum

class View(warehouse_view.DistrictOnlyView):

    def custom_context(self, request):
        product_types = list(ProductType.objects.filter(base_level=request.base_level))

        sp = SupplyPoint.objects.get(location=request.location) \
            if request.location else get_default_supply_point(request.user)
        
        selected_type = None
        if request.GET.get("product-type") in [ptype.code for ptype in product_types]:
            selected_type = ProductType.objects.get(code=request.GET["product-type"])
        
        products = Product.objects.filter(type=selected_type) if selected_type \
            else Product.objects.filter(type__base_level=request.base_level)
        products = products.order_by("sms_code")
        dates = get_datelist(request.datespan.startdate, 
                             request.datespan.enddate)
        
        data = defaultdict(lambda: defaultdict(lambda: 0)) 
        for p in products:
            for dt in dates:
                try:
                    of = OrderFulfillment.objects.get(supply_point=sp, product=p, date=dt)
                    data[p][dt] = of.average_fill_rate
                except OrderFulfillment.DoesNotExist:
                    # don't fail hard if a few product/location/date combinations don't exist
                    pass

        raw_graphdata = [
            {
                'data': [[i + 1, data[p][dt]] for i, dt in enumerate(dates)],
                'label': p.sms_code, 'lines': {"show": True},
                "bars": {"show": False}
            } for p in products
        ]
        
        graphdata = {
            "div": "order-fillrate-chart",
            "legenddiv": "order-fillrate-chart-legend",
            "legendcols": 10,
            "max_value": json.dumps(None),
            "xaxistitle": "month",
            "yaxistitle": "OFR %",
            "height": "350px",
            "width": "100%", 
            "xlabels": [[i + 1, '%s' % dt.strftime("%b")] for i, dt in enumerate(dates)],
            "data": json.dumps(raw_graphdata),
        }
        
        
        monthly_table = {
            "id": "monthly-average-ofr",
            "is_datatable": False,
            "is_downloadable": True,
            "header": ["Product"] + [dt.strftime("%B") for dt in dates], 
            "data": [[p.sms_code] + [fmt_or_none(data[p][dt]) for dt in dates] for p in products]
        }
        
        def _avg_fill_rate(f, p, dates):
            stats = OrderFulfillment.objects.filter\
                (supply_point=f, product=p, date__in=dates).aggregate\
                    (*[Sum(f) for f in ["quantity_requested", "quantity_received"]])
            return fmt_pct(stats["quantity_received__sum"] or 0,
                           stats["quantity_requested__sum"] or 0)  
        
        facility_table = None        
        if is_district(sp) or is_facility(sp):
            if is_district(sp):
                base_set = facility_supply_points_below(sp.location)
            else:
                assert is_facility(sp)
                base_set = hsa_supply_points_below(sp.location)
            facility_table = {
                "id": "ofr-facility-product",
                "is_datatable": True,
                "is_downloadable": True,
                "header": ["Facility"] + [p.sms_code for p in products],
                "data": [[f.name] + [_avg_fill_rate(f, p, dates) for p in products] \
                         for f in base_set.order_by('name')]
            }
        
        return {
            'product_types': product_types,
            'selected_type': selected_type,
            'graphdata': graphdata,
            'monthly_table': monthly_table,
            'facility_table': facility_table
        }
