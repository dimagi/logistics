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

    def get_stock_status_by_product_table(self, reporting_supply_point, is_facility):
        headings = [
            "Product",
            "AMC (last 60 days)",
            "TOTAL SOH (day of report)",
            "MOS (current period)",
            "Stock Status",
        ]
        status_data = get_stock_status_table_data(reporting_supply_point, is_facility=is_facility)
        return {
            "id": "product-table",
            "is_datatable": False,
            "is_downloadable": True,
            "header": headings,
            "data": status_data,
        }

    def get_months_of_stock_table(self, reporting_supply_point, is_facility):
        products = Product.objects.filter(is_active=True, type__is_facility=request.is_facility).order_by('sms_code')
        table = {
            "id": "months-of-stock-table",
            "is_datatable": True,
            "is_downloadable": True,
            "data": [],
            "location_type": "Facility" if is_facility else "HSA"
        }

        table["header"] = (
            [table["location_type"]] +
            [p.sms_code for p in products]
        )

        if is_facility:
            supply_points = hsa_supply_points_below(reporting_supply_point.location)
        else:
            supply_points = facility_supply_points_below(reporting_supply_point.location)

        for supply_point in supply_points:
            temp = [supply_point.name]
            for product in products:
                ps = ProductStock.objects.filter(supply_point=supply_point, product=product)
                if ps.count():
                    mr = ps[0].months_remaining
                    if mr:
                        temp.append('%.1f' % mr)
                    else:
                        temp.append('-')
                else:
                    temp.append('-')
            table["data"].append(temp)

        return table

    def get_stock_status_across_location_table(self, request, reporting_supply_point, selected_product, is_facility):
        table = {
            "id": "location-table",
            "is_datatable": True,
            "is_downloadable": True,
        }
        reporter = 'Facility' if is_facility else 'HSA'
        headings = [(header % reporter) for header in [
            "%% %s Stocked Out",
            "%% %s Under",
            "%% %s Adequate",
            "%% %s Overstocked",
            "%% %s Not Reported",
        ]]

        if is_district(reporting_supply_point):
            table["location_type"] = "Facility"
            table["header"] = [table["location_type"]] + headings
            table["data"] = self._get_product_status_table(
                facility_supply_points_below(reporting_supply_point.location).order_by('name'),
                selected_product,
                current_report_period(),
            )
        elif is_country(reporting_supply_point):
            table["location_type"] = "District"
            table["header"] = [table["location_type"]] + headings
            table["data"] = self._get_product_status_table(
                get_district_supply_points(request.user.is_superuser).order_by('name'),
                selected_product,
                current_report_period(),
            )

        return table

    def custom_context(self, request):
        selected_type = self.get_selected_product_type(request)
        selected_product = self.get_selected_product(request)
        reporting_supply_point = self.get_reporting_supply_point(request)

        months_of_stock_table = None
        stock_status_across_location_table = None

        if (
            (is_facility(reporting_supply_point) and not request.is_facility) or
            (is_district(reporting_supply_point) and request.is_facility)
        ):
            months_of_stock_table = self.get_months_of_stock_table(reporting_supply_point, request.is_facility)
        else:
            if is_district(reporting_supply_point) or is_country(reporting_supply_point):
                stock_status_across_location_table = self.get_stock_status_across_location_table(
                    request,
                    reporting_supply_point,
                    selected_product,
                    request.is_facility
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
            'status_table': self.get_stock_status_by_product_table(reporting_supply_point, request.is_facility),
            'stock_status_across_location_table': stock_status_across_location_table,
            'hsa_stockouts': hsa_stockouts,
            'months_of_stock_table': months_of_stock_table,
            'graphdata': graph_chart,
            'is_facility': request.is_facility,
        }
