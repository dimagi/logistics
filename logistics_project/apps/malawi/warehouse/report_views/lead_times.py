from collections import defaultdict
from datetime import datetime

from logistics.models import SupplyPoint

from dimagi.utils.dates import months_between

from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.util import get_country_sp,\
    facility_supply_points_below
from static.malawi.config import TimeTrackerTypes
from logistics_project.apps.malawi.warehouse.models import TimeTracker,\
    TIME_TRACKER_TYPES
import json
from django.db.models import Sum


class View(warehouse_view.DistrictOnlyView):

    def custom_context(self, request):
        sp = SupplyPoint.objects.get(location=request.location) \
            if request.location else get_country_sp()
        
        data = defaultdict(lambda: defaultdict(lambda: 0)) # turtles!
        dates = [datetime(year, month, 1) for year, month in \
                 months_between(request.datespan.startdate, 
                                request.datespan.enddate)]
        
        for dt in dates:
            for code, name in TIME_TRACKER_TYPES:
                data[code][dt] = TimeTracker.objects.get\
                    (supply_point=sp, date=dt, type=code).avg_time_in_days
            
        ret_data = [{'data': [[i + 1, data[code][dt]] for i, dt in enumerate(dates)],
                     'label': name, 'lines': {"show": False}, "bars": {"show": True},
                     'stack': 0} \
                     for code, name in TIME_TRACKER_TYPES]
        report_chart = {
            "legenddiv": "leadtime-legend-div",
            "div": "leadtime-chart-div",
            "width": "100%",
            "height": "200px",
            "xaxistitle": "month",
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
            "title": "",
            "header": ['Month', 'Ord-Ord Ready (days)', 'Ord-Ord Received (days)', 
                       'Total Lead Time (days)'],
            "data": rows
        }
        
        def _to_days(secs, count):
            if count:
                return float(secs) / float(count * 60 * 60 * 24)
            return None
        
        f_data = []
        for f in facility_supply_points_below(sp.location).order_by('name'):
            matching = TimeTracker.objects.filter(supply_point=f,
                                                  date__gte=request.datespan.startdate,
                                                  date__lte=request.datespan.enddate)
            or_tots = matching.filter(type=TimeTrackerTypes.ORD_READY).aggregate\
                (Sum('total'), Sum('time_in_seconds'))
            avg_or_lt = _to_days(or_tots["time_in_seconds__sum"], or_tots["total__sum"])
            rr_tots = matching.filter(type=TimeTrackerTypes.READY_REC).aggregate\
                (Sum('total'), Sum('time_in_seconds'))
            avg_rr_lt = _to_days(rr_tots["time_in_seconds__sum"], rr_tots["total__sum"])
            avg_tot_lt = avg_or_lt + avg_rr_lt if avg_or_lt is not None and avg_rr_lt is not None else None
            f_data.append([f.name, len(dates)] + [_table_fmt(val) for val in \
                                      (avg_or_lt, avg_rr_lt, avg_tot_lt)])
            
        lt_table = {
            "id": "average-lead-times-facility",
            "is_datatable": True,
            "header": ['Facility', 'Period (# Months)', 'Ord-Ord Ready (days)', 'Ord-Ord Received(days)', 'Total Lead Time (days)'],
            "data": f_data,
        }    
        return {"graphdata": report_chart,
                "month_table": month_table,
                "lt_table": lt_table}
