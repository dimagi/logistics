from datetime import datetime
from collections import defaultdict, OrderedDict


from logistics_project.utils.dates import months_between

from logistics.models import SupplyPoint

from logistics_project.apps.malawi.util import (get_default_supply_point,
    get_district_supply_points, facility_supply_points_below, fmt_pct,
    hsa_supply_points_below, is_country, is_district, is_facility,
    filter_district_queryset_for_epi)
from logistics_project.apps.malawi.warehouse.models import ReportingRate
from logistics_project.apps.malawi.warehouse.report_utils import get_reporting_rates_chart
from logistics_project.apps.malawi.warehouse import warehouse_view


class View(warehouse_view.DistrictOnlyView):

    automatically_adjust_datespan = True

    def custom_context(self, request):
        shared_headers = ["% Reporting", "% On time Rep", "% Late Rep", "% Not Reported", "% Complete"]
        shared_slugs = ["reported", "on_time", "late", "missing", "complete"]
        
        # reporting rates by month table
        sp = SupplyPoint.objects.get(location=request.location) \
            if request.location else get_default_supply_point(request.user)
        
        months = OrderedDict()
        for year, month in months_between(request.datespan.startdate, 
                                          request.datespan.enddate):
            dt = datetime(year, month, 1)
            months[dt] = ReportingRate.objects.get(supply_point=sp, date=dt, base_level=request.base_level)

        month_data = [
            [dt.strftime("%B")] + [getattr(rr, "pct_%s" % k) for k in shared_slugs]
            for dt, rr in list(months.items())
        ]

        month_table = {
            "id": "month-table",
            "is_datatable": False,
            "is_downloadable": True,
            "header": ["Months"] + shared_headers,
            "data": month_data,
        }

        def _avg_report_rate_table_data(queryset, startdate, enddate):
            datamap = OrderedDict()
            for sp in queryset:
                spdata = defaultdict(lambda: 0)
                for year, month in months_between(startdate, 
                                                  enddate):
                    try:
                        rr = ReportingRate.objects.get(supply_point=sp,
                                                       date=datetime(year, month, 1),
                                                       base_level=request.base_level)
                        spdata['total'] += rr.total
                        for k in shared_slugs:
                            spdata[k] += getattr(rr, k)
                    except ReportingRate.DoesNotExist:
                        pass # hopefully just a new facility or otherwise not-warehoused thing
                    
                datamap[sp] = spdata
                        
            return [
                [sp.name] +
                [fmt_pct(data[k], data['reported'] if k == 'complete' else data['total']) for k in shared_slugs]
                for sp, data in list(datamap.items())
            ]

        location_table = None
        if is_country(sp):
            # district breakdown
            districts = get_district_supply_points(request.user.is_superuser).order_by('name')
            if request.base_level_is_facility:
                districts = filter_district_queryset_for_epi(districts)
            location_table = {
                "id": "average-reporting-rate-districts",
                "is_datatable": False,
                "is_downloadable": True,
                "header": ["Districts"] + shared_headers,
                "data": _avg_report_rate_table_data(districts,
                                                    request.datespan.startdate,
                                                    request.datespan.enddate),
                "location_type": "districts"
            }
        elif is_district(sp):
            # facility breakdown
            location_table = {
                "id": "average-reporting-rate-facilities",
                "is_datatable": False,
                "is_downloadable": True,
                "header": ["Facilities"] + shared_headers,
                "data": _avg_report_rate_table_data(
                    facility_supply_points_below(sp.location).order_by('name'),
                    request.datespan.startdate,
                    request.datespan.enddate
                ),
                "location_type": "facilities"
            }

        hsa_table = None
        if is_facility(sp):
            hsa_table = {
                "id": "hsa-reporting-profiles",
                "is_datatable": True,
                "is_downloadable": True,
                "header": ["HSA", "Min Number expected", "Non-reporting", "On Time", "Late", "Complete"],
                "data": []
            }

            hsas = hsa_supply_points_below(sp.location)
            for hsa in hsas:
                rr = ReportingRate.objects.filter(
                    supply_point=hsa,
                    date__range=(request.datespan.startdate, request.datespan.enddate),
                    base_level=request.base_level,
                )
                total = non_rep = on_time = late = complete = 0
                for r in rr:
                    total += r.total
                    non_rep += r.missing
                    on_time += r.on_time
                    late += r.late
                    complete += r.complete
                hsa_table["data"].append([hsa.name, total, non_rep, on_time, late, complete])

        return {
            "month_table": month_table,
            "location_table": location_table,
            "hsa_table": hsa_table,
            "graphdata": get_reporting_rates_chart(request.location,
                                                   request.datespan.startdate,
                                                   request.datespan.enddate,
                                                   base_level=request.base_level)
        }
