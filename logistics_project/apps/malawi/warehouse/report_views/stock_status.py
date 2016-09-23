import json
from collections import defaultdict

from logistics.models import Product, SupplyPoint, ProductType, ProductStock

from logistics_project.apps.malawi.util import get_default_supply_point, fmt_pct, pct,\
    is_country, is_district, is_facility, hsa_supply_points_below,\
    facility_supply_points_below, get_district_supply_points
from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.warehouse.report_utils import get_datelist,\
    get_stock_status_table_data, current_report_period
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData
from django.db.models.aggregates import Sum
from django.shortcuts import get_object_or_404

class View(warehouse_view.DistrictOnlyView):

    def _get_product_status_table(self, supply_points, product, date):
        ret = []
        for s in supply_points:
            qs = ProductAvailabilityData.objects.filter(supply_point=s, product=product, date=date)
            values = qs.aggregate(Sum('managed_and_without_stock'),
                                  Sum('managed_and_under_stock'),
                                  Sum('managed_and_good_stock'),
                                  Sum('managed_and_over_stock'),
                                  Sum('managed_and_without_data'),
                                  Sum('managed'))
            ret.append([
                 s.name,
                 fmt_pct(values["managed_and_without_stock__sum"] or 0, values["managed__sum"] or 0),
                 fmt_pct(values["managed_and_under_stock__sum"] or 0, values["managed__sum"] or 0),
                 fmt_pct(values["managed_and_good_stock__sum"] or 0, values["managed__sum"] or 0),
                 fmt_pct(values["managed_and_over_stock__sum"] or 0, values["managed__sum"] or 0),
                 fmt_pct(values["managed_and_without_data__sum"] or 0, values["managed__sum"] or 0),
            ])
        return ret

    def get_selected_product_type(self, request):
        typecode = request.GET.get("product-type")
        if typecode:
            return get_object_or_404(ProductType, code=typecode, is_facility=request.is_facility)

        return None

    def get_selected_product(self, request):
        pcode = request.GET.get("product")
        if pcode:
            return get_object_or_404(Product, sms_code=pcode, type__is_facility=request.is_facility)

        return Product.objects.filter(type__is_facility=request.is_facility)[0]

    def get_reporting_supply_point(self, request):
        if request.location:
            return SupplyPoint.objects.get(location=request.location)

        return get_default_supply_point(request.user)

    def custom_context(self, request):
        selected_type = self.get_selected_product_type(request)
        selected_product = self.get_selected_product(request)
        reporting_supply_point = self.get_reporting_supply_point(request)

        headings = ["% HSA Stocked Out", "% HSA Under", "% HSA Adequate", 
                    "% HSA Overstocked", "% HSA Not Reported"]
        
        # data by product
        new_headings = ["Product", "AMC (last 60 days)",
                        "TOTAL SOH (day of report)", "MOS (current period)",
                        "Stock Status"]
        status_data = get_stock_status_table_data(reporting_supply_point, is_facility=request.is_facility)
        status_table = {
            "id": "product-table",
            "is_datatable": False,
            "is_downloadable": True,
            "header": new_headings,
            "data": status_data,
        }
            
        hsa_table = None
        location_table = {
            "id": "location-table",
            "is_datatable": True,
            "is_downloadable": True,
        }
            
        if is_facility(reporting_supply_point):
            products = Product.objects.filter(is_active=True, type__is_facility=request.is_facility).order_by('sms_code')
            hsa_table = {
                "id": "hsa-table",
                "is_datatable": True,
                "is_downloadable": True,
                "data": [],
                "location_type": "HSA"
            }
            
            hsa_table["header"] = [hsa_table["location_type"]] + \
                [p.sms_code for p in products]
            
            # this chart takes a long time to load
            hsas = hsa_supply_points_below(reporting_supply_point.location)
            for hsa in hsas:
                temp = [hsa.name]
                for product in products:
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

            location_table = {} # don't show the location table for HSA's only
        elif is_country(reporting_supply_point):
            location_table["location_type"] = "District"
            location_table["header"] = [location_table["location_type"]] + headings
            location_table["data"] = self._get_product_status_table(
                get_district_supply_points(request.user.is_superuser).order_by('name'),
                selected_product,
                current_report_period(),
            )

            
        else:
            assert is_district(reporting_supply_point)
            location_table["location_type"] = "Facility"
            location_table["header"] = [location_table["location_type"]] + headings
            location_table["data"] = self._get_product_status_table(
                facility_supply_points_below(reporting_supply_point.location).order_by('name'),
                selected_product,
                current_report_period(),
            )

        data = defaultdict(lambda: defaultdict(lambda: 0)) 
        dates = get_datelist(request.datespan.startdate, 
                             request.datespan.enddate)
        
        # product line chart 
        hsa_stockouts = {
            "id": "hsa-stockouts",
            "header": ['Product'] + [dt.strftime("%b %Y") for dt in dates],
        }
        hsa_stockout_data = []
        active = Product.objects.filter(is_active=True, type__is_facility=request.is_facility)
        products = active.objects.filter(type=selected_type) if selected_type else active
        for p in products:
            nums = []
            denoms = []
            for dt in dates:
                try:
                    pad = ProductAvailabilityData.objects.get(supply_point=reporting_supply_point, product=p, date=dt)
                    data[p][dt] = pct(pad.managed_and_without_stock, pad.managed)
                    nums.append(pad.managed_and_without_stock)
                    denoms.append(pad.managed)
                except ProductAvailabilityData.DoesNotExist:
                    data[p][dt] = 0
                    nums.append(0)
                    denoms.append(0)

            hsa_stockout_data.append(['%s - num' % p.name] + nums)
            hsa_stockout_data.append(['%s - denom' % p.name] + denoms)
            hsa_stockout_data.append(['%s - pct' % p.name] + [pct(nums[i], denoms[i]) for i in range(len(nums))])

        hsa_stockouts['data'] = hsa_stockout_data
        graph_data = [{'data': [[i + 1, data[p][dt]] for i, dt in enumerate(dates)],
                       'label': p.sms_code, 'lines': {"show": True}, 
                       "bars": {"show": False}} \
                       for p in products]
        graph_chart = {
            "div": "product-stockouts-chart",
            "legenddiv": "product-stockouts-chart-legend",
            "legendcols": 10,
            "yaxistitle": "% SO",
            "height": "350px",
            "width": "100%", # "300px",
            "xlabels": [[i + 1, dt.strftime("%b")] for i, dt in enumerate(dates)],
            "data": json.dumps(graph_data),
        }

        return {
            'product_types': ProductType.objects.filter(is_facility=request.is_facility),
            'window_date': current_report_period(),
            'selected_type': selected_type,
            'selected_product': selected_product,
            'status_table': status_table,
            'location_table': location_table,
            'hsa_stockouts': hsa_stockouts,
            'hsa_table': hsa_table,
            'graphdata': graph_chart,
            'is_facility': request.is_facility,
        }
