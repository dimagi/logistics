import json
from collections import defaultdict
from datetime import datetime

from django.db.models import Sum

from logistics_project.utils.dates import months_between

from logistics.util import config
from logistics.models import SupplyPoint

from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.util import get_default_supply_point,\
    facility_supply_points_below, hsa_supply_points_below, get_district_supply_points
from logistics_project.apps.malawi.warehouse.models import TimeTracker,\
    TIME_TRACKER_TYPES

from static.malawi.config import TimeTrackerTypes
from logistics_project.apps.malawi.warehouse.report_utils import get_lead_time_table_data


class View(warehouse_view.DistrictOnlyView):

    def custom_context(self, request):
        sp = SupplyPoint.objects.get(location=request.location) \
            if request.location else get_default_supply_point(request.user)
        
        data = defaultdict(lambda: defaultdict(lambda: 0)) # turtles!
        dates = [datetime(year, month, 1) for year, month in \
                 months_between(request.datespan.startdate, 
                                request.datespan.enddate)]
        
        for dt in dates:
            for code, name in TIME_TRACKER_TYPES:
                data[code][dt] = TimeTracker.objects.get\
                    (supply_point=sp, date=dt, type=code).avg_time_in_days or 0
            
        ret_data = [{'data': [[i + 1, data[code][dt]] for i, dt in enumerate(dates)],
                     'label': name, 'lines': {"show": False}, "bars": {"show": True, "fill": 1 },
                     'stack': 0} \
                     for code, name in TIME_TRACKER_TYPES]

        report_chart = {
            "legenddiv": "leadtime-legend-div",
            "div": "leadtime-chart-div",
            "width": "100%",
            "height": "200px",
            "xaxistitle": "month",
            "yaxistitle": "# days",
            "xlabels": [[i + 1, '%s' % dt.strftime("%b")] for i, dt in enumerate(dates)],
            "data": json.dumps(ret_data)
        }
        
        def _table_fmt(val):
            if val is not None:
                return "%.1f" % val
            return "No data"
        
        rows = []
        for dt in dates:
            or_days = data[TimeTrackerTypes.ORD_READY][dt] 
            rr_days = data[TimeTrackerTypes.READY_REC][dt] 
            tot_days = or_days + rr_days if or_days is not None and rr_days is not None else None
            rows.append([dt.strftime("%b")] + [_table_fmt(val) for val in \
                                               (or_days, rr_days, tot_days)])
        month_table = {
            "id": "month-table",
            "is_datatable": False,
            "is_downloadable": True,
            "header": ['Month', 'Order - Ready (days)', 'Ready - Received (days)', 
                       'Total Lead Time (days)'],
            "data": rows
        }
        
        

        dis_lt_table = fac_lt_table = hsa_lt_table = None
        if sp.type.code == config.SupplyPointCodes.COUNTRY:
            d_data = get_lead_time_table_data(get_district_supply_points(request.user.is_superuser).order_by('name'),
                                              request.datespan.startdate, request.datespan.enddate)

            dis_lt_table = {
                "id": "average-lead-times-district",
                "is_datatable": True,
                "is_downloadable": True,
                "header": ['Facility', 'Order - Ready (days)', 'Ready - Received (days)', 'Total Lead Time (days)'],
                "data": d_data,
            }   

        if sp.type.code == config.SupplyPointCodes.DISTRICT:
            f_data = get_lead_time_table_data(facility_supply_points_below(sp.location).order_by('name'),
                                              request.datespan.startdate, request.datespan.enddate)

            fac_lt_table = {
                "id": "average-lead-times-facility",
                "is_datatable": True,
                "is_downloadable": True,
                "header": ['Facility', 'Ord-Ord Ready (days)', 'Ord-Ord Received(days)', 'Total Lead Time (days)'],
                "data": f_data,
            }   

        if sp.type.code == config.SupplyPointCodes.FACILITY:
            h_data = get_lead_time_table_data(hsa_supply_points_below(sp.location).order_by('name'),
                                              request.datespan.startdate, request.datespan.enddate)

            hsa_lt_table = {
                "id": "average-lead-times-hsa",
                "is_datatable": True,
                "is_downloadable": True,
                "header": ['HSA', 'Ord-Ord Ready (days)', 'Ord-Ord Received(days)', 'Total Lead Time (days)'],
                "data": h_data,
            }   

        return {
                "graphdata": report_chart,
                "month_table": month_table,
                "district_lt_table": dis_lt_table,
                "fac_lt_table": fac_lt_table,
                "hsa_lt_table": hsa_lt_table,
        }
