from datetime import datetime

from django.utils.datastructures import SortedDict

from dimagi.utils.dates import months_between, DateSpan, add_months

from logistics.models import SupplyPoint
from logistics.util import config

from logistics_project.apps.malawi.util import get_country_sp,\
    get_district_supply_points, facility_supply_points_below
from logistics_project.apps.malawi.warehouse.models import ReportingRate
from logistics_project.apps.malawi.warehouse.report_utils import get_reporting_rates_chart


def get_context(request):
    ret_obj = {}
    summary = {
        "number": 3,
        "xlabels": [],
        "legenddiv": "legend-div",
        "div": "chart-div",
        "max_value": 3,
        "width": "100%",
        "height": "200px",
        "data": [],
        "xaxistitle": "products",
        "yaxistitle": "amount"
    }
    shared_headers = ["% Reporting", "% Rep on time", "% Late Rep", "% No Rep", "% Complete"]
    shared_slugs = ["reported", "on_time", "late", "missing", "complete"]
    
    # reporting rates by month table
    sp = SupplyPoint.objects.get(location=request.location) \
        if request.location else get_country_sp()
    months = SortedDict()
    for year, month in months_between(request.datespan.startdate, request.datespan.enddate):
        dt = datetime(year, month, 1)
        months[dt] = ReportingRate.objects.get(supply_point=sp, date=dt)
    
    month_data = [[dt.strftime("%B")] + [getattr(rr, "pct_%s" % k) for k in shared_slugs] \
                  for dt, rr in months.items()]
    
    ret_obj['month_table'] = {
        "title": "",
        "header": ["Months"] + shared_headers,
        "data": month_data,
    }

    # district breakdown
    d_rr_pairs = [[d, ReportingRate.objects.get(supply_point=d, 
                                                date=request.datespan.enddate)] \
                  for d in get_district_supply_points().order_by('name')]
                                                
    district_data = [[d.name] + [getattr(rr, "pct_%s" % k) for k in shared_slugs] \
                     for d, rr in d_rr_pairs]
    
    ret_obj['district_table'] = {
        "title": "Average Reporting Rate (Districts)",
        "header": ["Districts"] + shared_headers,
        "data": district_data,
    }
    
    if sp.type.code == config.SupplyPointCodes.DISTRICT:
        f_rr_pairs = [[f, ReportingRate.objects.get(supply_point=f, 
                                                    date=request.datespan.enddate)] \
                      for f in facility_supply_points_below(sp.location).order_by('name')]
                                                    
        print f_rr_pairs
        fac_data = [[f.name] + [getattr(rr, "pct_%s" % k) for k in shared_slugs] \
                         for f, rr in f_rr_pairs]
        
        ret_obj['facility_table'] = {
            "title": "Average Reporting Rate (Facilities)",
            "header": ["Facilities"] + shared_headers,
            "data": fac_data,
        }
    ret_obj['graphdata'] = get_reporting_rates_chart(request.location, 
                                                     request.datespan.startdate, 
                                                     request.datespan.enddate)
    return ret_obj