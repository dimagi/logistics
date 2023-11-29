from __future__ import unicode_literals
from builtins import range
import json
import folium
import logging
import random
from collections import defaultdict
from geopy.geocoders import Nominatim

from logistics.models import (Product, SupplyPoint, SupplyPointType,
                              ProductType, ProductStock)
from logistics.util import config
from logistics_project.apps.malawi.util import (fmt_pct, pct,
    is_country, is_district, is_facility, hsa_supply_points_below,
    facility_supply_points_below, get_district_supply_points,
    filter_district_queryset_for_epi)
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
            return get_object_or_404(ProductType, code=typecode, base_level=request.base_level)

        return None

    def get_selected_product(self, request, element_id="product"):
        pcode = request.GET.get(element_id)
        if pcode:
            return get_object_or_404(Product, sms_code=pcode, type__base_level=request.base_level)

        return Product.objects.filter(type__base_level=request.base_level)[0]

    def get_stock_status_by_product_table(self, request, reporting_supply_point):
        headings = [
            "Product",
            "AMC (last 60 days)",
            "TOTAL SOH (day of report)",
            "MOS (current period)",
            "Stock Status",
        ]
        status_data = get_stock_status_table_data(reporting_supply_point, base_level=request.base_level)
        return {
            "id": "product-table",
            "is_datatable": False,
            "is_downloadable": True,
            "header": headings,
            "data": status_data,
        }

    def get_months_of_stock_table(self, request, reporting_supply_point):
        products = Product.objects.filter(is_active=True, type__base_level=request.base_level).order_by('sms_code')
        table = {
            "id": "months-of-stock-table",
            "is_datatable": True,
            "is_downloadable": True,
            "data": [],
            "location_type": config.BaseLevel.get_base_level_description(request.base_level),
        }

        table["header"] = (
            [table["location_type"]] +
            [p.sms_code for p in products]
        )

        if request.base_level_is_hsa:
            supply_points = hsa_supply_points_below(reporting_supply_point.location)
        elif request.base_level_is_facility:
            supply_points = facility_supply_points_below(reporting_supply_point.location)
        else:
            raise config.BaseLevel.InvalidBaseLevelException(request.base_level)

        for supply_point in supply_points:
            temp = [supply_point.name]
            for product in products:
                ps = ProductStock.objects.filter(supply_point=supply_point, product=product)
                if ps.count():
                    mr = ps[0].months_remaining
                    if mr is not None:
                        temp.append('%.1f' % mr)
                    else:
                        temp.append('-')
                else:
                    temp.append('-')
            table["data"].append(temp)

        return table

    def get_stock_status_across_location_table(self, request, reporting_supply_point, selected_product):
        table = {
            "id": "location-table",
            "is_datatable": True,
            "is_downloadable": True,
        }
        reporter = config.BaseLevel.get_base_level_description(request.base_level)
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
            districts = get_district_supply_points(request.user.is_superuser).order_by('name')
            if request.base_level_is_facility:
                districts = filter_district_queryset_for_epi(districts)
            table["data"] = self._get_product_status_table(
                districts,
                selected_product,
                current_report_period(),
            )

        return table

    def get_stockout_report(self, request, reporting_supply_point, selected_type):
        data = defaultdict(lambda: defaultdict(lambda: 0)) 
        dates = get_datelist(
            request.datespan.startdate,
            request.datespan.enddate
        )

        table = {
            "id": "stockout-table",
            "header": ['Product'] + [dt.strftime("%b %Y") for dt in dates],
        }
        stockout_data = []
        active = Product.objects.filter(is_active=True, type__base_level=request.base_level)
        products = active.filter(type=selected_type) if selected_type else active

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

            stockout_data.append(['%s - num' % p.name] + nums)
            stockout_data.append(['%s - denom' % p.name] + denoms)
            stockout_data.append(['%s - pct' % p.name] + [pct(nums[i], denoms[i]) for i in range(len(nums))])

        table['data'] = stockout_data

        graph_data = [{'data': [[i + 1, data[p][dt]] for i, dt in enumerate(dates)],
                       'label': p.sms_code, 'lines': {"show": True}, 
                       "bars": {"show": False}} \
                       for p in products]

        graph = {
            "div": "product-stockouts-chart",
            "legenddiv": "product-stockouts-chart-legend",
            "legendcols": 10,
            "yaxistitle": "% SO",
            "height": "350px",
            "width": "100%",
            "xlabels": [[i + 1, dt.strftime("%b")] for i, dt in enumerate(dates)],
            "data": json.dumps(graph_data),
        }

        return table, graph

    def is_viewing_base_level_data(self, request, reporting_supply_point):
        return (
            (is_facility(reporting_supply_point) and request.base_level_is_hsa) or
            (is_district(reporting_supply_point) and request.base_level_is_facility)
        )

    def get_stock_status_map(self, request, reporting_supply_point, selected_product):
        """
        Status of product in map format.

        """
        product_map = folium.Map(location=(-13.9626, 33.7741), zoom_start=6)

        try:
            # Retrieve active product stock per supply point including location coordinates
            # 1. Retrieve active supply points at hsa level
            hsa_sup_type = SupplyPointType.objects.get(pk='hsa')
            suppliers = SupplyPoint.objects.filter(active=True, type=hsa_sup_type)

            # 2. Retrieve product details including stock levels
            product = Product.by_code(selected_product.sms_code)
            product_suppliers = [sup for sup in suppliers if sup.supplies(product)]

            # 3. Obtain location point details for each supply point if available
            for supplier in product_suppliers:
                # retrieve location coordinates if set otherwise do not display
                if supplier.location.point:
                    location_point = supplier.location.point
                else:
                    continue

                # 4. indicate stock levels using color codes
                current_stock = ProductStock.objects.get(supply_point=supplier, product=product)
                current_quantity = current_stock.quantity
                product_amc = product.average_monthly_consumption
                product_eo_level = product.emergency_order_level

                # only mark location if quantity, and either amc or eo level are set
                if current_quantity:
                    # if both amc and eo level set then any status can be set
                    if product_amc and product_eo_level:
                        if current_quantity >= product_amc:
                            stock_status_color = 'green'
                        elif current_quantity <= product_eo_level:
                            stock_status_color = 'red'
                        else:
                            stock_status_color = 'blue'
                    elif product_amc and product_eo_level is None:
                        # if only product amc then either above amc or below
                        if current_quantity >= product_amc:
                            stock_status_color = 'green'
                        else:
                            stock_status_color = 'red'
                    else:
                        continue

                    # Define marker using supplier name, quantity, and stock status
                    label = f'{supplier.name} ({current_quantity})'

                    if location_point:
                        folium.Marker(
                            location=[location_point.latitude,
                                      location_point.longitude],
                            tooltip=label,
                            popup=label,
                            icon=folium.Icon(color=stock_status_color)
                        ).add_to(product_map)
        except Product.DoesNotExist:
            pass
        except ProductStock.DoesNotExist:
            pass

        return product_map._repr_html_()

    def custom_context(self, request):
        selected_type = self.get_selected_product_type(request)
        selected_product = self.get_selected_product(request)
        selected_map_product = self.get_selected_product(request, "map_product")
        reporting_supply_point = self.get_reporting_supply_point(request)

        product_map = self.get_stock_status_map(request, reporting_supply_point,
                                                selected_map_product)

        months_of_stock_table = None
        stock_status_across_location_table = None

        if self.is_viewing_base_level_data(request, reporting_supply_point):
            months_of_stock_table = self.get_months_of_stock_table(request, reporting_supply_point)

        if is_district(reporting_supply_point) or is_country(reporting_supply_point):
            stock_status_across_location_table = self.get_stock_status_across_location_table(
                request,
                reporting_supply_point,
                selected_product
            )

        stockout_table, stockout_graph = self.get_stockout_report(request, reporting_supply_point,
            selected_type)

        return {
            'product_types': ProductType.objects.filter(base_level=request.base_level),
            'window_date': current_report_period(),
            'selected_type': selected_type,
            'selected_product': selected_product,
            'selected_map_product': selected_map_product,
            'status_table': self.get_stock_status_by_product_table(request, reporting_supply_point),
            'stock_status_across_location_table': stock_status_across_location_table,
            # This apparently isn't used in the template but is needed in get_report() when export_csv=True
            'stockout_table': stockout_table,
            'months_of_stock_table': months_of_stock_table,
            'stockout_graph': stockout_graph,
            'product_map': product_map
        }
