'''
New views for the upgraded reports of the system.
'''
from random import random
from datetime import datetime, timedelta

from django.conf import settings
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect
from django.utils.datastructures import SortedDict

from dimagi.utils.decorators.datespan import datespan_in_request
from dimagi.utils.dates import months_between

from rapidsms.contrib.locations.models import Location

from logistics.models import Product, SupplyPoint
from logistics.decorators import place_in_request

from logistics_project.apps.malawi.util import get_facilities, get_districts
from logistics.util import config
from logistics_project.apps.malawi.warehouse_models import ProductAvailabilityData,\
    ProductAvailabilityDataSummary, ReportingRate

REPORT_LIST = SortedDict([
    ("Dashboard", "dashboard"),
    ("Reporting Rate", "reporting-rate"),
    ("Stock Status", "stock-status"),
    ("Consumption Profiles", "consumption-profiles"),
    ("Alert Summary", "alert-summary"),
    ("Re-supply Qts Required", "re-supply-qts-required"),
    ("Lead Times", "lead-times"),
    ("Order Fill Rate", "order-fill-rate"),
    ("Emergency Orders", "emergency-orders"),
])

to_stub = lambda x: {"name": x, "slug": REPORT_LIST[x]}

stub_reports = [to_stub(r) for r in REPORT_LIST.keys()]

def home(request):
    return redirect("/malawi/r/dashboard/")
    
@place_in_request()
@datespan_in_request(format_string='%B %Y')
def get_report(request, slug=''):
    context = shared_context(request)
    context.update({"report_list": stub_reports,
                    "slug": slug})
    
    context.update(get_more_context(slug))

    return render_to_response("malawi/new/%s.html" % slug, 
                              context,
                              context_instance=RequestContext(request))

def get_more_context(slug):
    func_map = {
        'dashboard': dashboard_context,
        'emergency-orders': eo_context,
        'order-fill-rate': ofr_context,
        're-supply-qts-required': rsqr_context,
        'alert-summary': as_context,
        'consumption-profiles': cp_context,
        'stock-status': ss_context,
        'lead-times': lt_context,
        'reporting-rate': rr_context,
    }
    if slug in func_map:
        return func_map[slug]()
    else:
        return {}


def shared_context(request):
    products = Product.objects.all().order_by('sms_code')
    country = SupplyPoint.objects.get(code__iexact=settings.COUNTRY,
                                      type__code=config.SupplyPointCodes.COUNTRY)
    window_date = _get_window_date(request)
    
    # national stockout percentages by product
    stockout_pcts = SortedDict()
    for p in products:
        availability = ProductAvailabilityData.objects.get(supply_point=country,
                                                           date=window_date,
                                                           product=p)
        stockout_pcts[p] = _pct(availability.managed_and_without_stock,
                                availability.managed)
    
    return { "settings": settings,
             "location": None,
             "districts": get_districts(),
             "facilities": get_facilities(),
             "hsas": 643,
             "reporting_rate": "93.3",
             "products": products,
             "product_stockout_pcts": stockout_pcts
    }

def timechart(labels):
    summary = {
        "xlabels": [],
        "legenddiv": "legend-div",
        "div": "chart-div",
        "max_value": 3,
        # "width": "730px",
        "width": "100%",
        "height": "200px",
        "data": [],
        "xaxistitle": "month",
        "yaxistitle": "rate"
    }
    count = 0
    for year, month in months_between(datetime.now() - timedelta(days=61), datetime.now()):
        count += 1
        summary['xlabels'].append([count, '<span>%s</span>' % datetime(year, month, 1).strftime("%b")])
        
    summary['data'] = barseries(labels, len(summary['xlabels']))
    return summary


def barseries(labels, num_points):
    return [{"label": l, "data": bardata(num_points)} for l in labels]
    
def bardata(num_points):
    return [[i + 1, random()] for i in range(num_points)]


def lt_context():
    month_table = {
        "title": "",
        "header": ['Month', 'Ord-Ord Ready (days)', 'Ord-Ord Received(days)', 'Total Lead Time (days)'],
        "data": [['Jan', 3, 14, 7], ['Feb', 12, 7, 4], ['Mar', 14, 6, 4]],
    }

    lt_table = {
        "title": "Average Lead Times by Facility",
        "header": ['Facility', 'Period (# Months)', 'Ord-Ord Ready (days)', 'Ord-Ord Received(days)', 'Total Lead Time (days)'],
        "data": [['BULA', 6, 31, 42, 37], ['Chesamu', 6, 212, 27, 14], ['Chikwina', 6, 143, 61, 14]],
    }    
    return {"summary": timechart(['Ord-Ord Ready', 'Ord-Ord Received']),
            "month_table": month_table,
            "lt_table": lt_table}

def dashboard_context():
    window_date = _get_window_date()
    
    # reporting rates + stockout summary
    districts = get_districts().order_by('name')
    summary_data = SortedDict()
    for d in districts:
        avail_sum = ProductAvailabilityDataSummary.objects.get(supply_point=d, date=window_date)
        stockout_pct = _pct(avail_sum.with_any_stockout,
                             avail_sum.manages_anything) 
        rr = ReportingRate.objects.get(supply_point=d, date=window_date)
        reporting_rate = _pct(rr.reported, rr.total)
        summary_data[d] = {"stockout_pct": stockout_pct,
                           "reporting_rate": reporting_rate}
    
    return {"summary_data": summary_data,
            "summary": timechart(['on time','late','not reported']),
            "pa_width": 530 if settings.STYLE=='both' else 730 }

def eo_context():
    ret_obj = {}
    summary = {
        "product_codes": [],
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
    
    count = 0
    for product in Product.objects.all().order_by('sms_code')[0:10]:
        count += 1
        summary['product_codes'].append([count, '<span>%s</span>' % (str(product.code.lower()))])
        summary['xlabels'] = summary['product_codes']
    
    summary['data'] = barseries(['a','b','c'], 10)

    table = {
        "title": "%HSA with Emergency Order by Product",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 35, 41, 53, 34], ['dt', 26, 26, 44, 21], ['sr', 84, 24, 54, 36]],
        "cell_width": "135px",
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

    ret_obj['summary'] = summary
    ret_obj['table'] = table
    ret_obj['line'] = line_chart
    return ret_obj


def ofr_context():
    ret_obj = {}

    table1 = {
        "title": "Monthly Average OFR by Product (%)",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 32, 41, 54, 35], ['dt', 23, 22, 41, 16], ['sr', 45, 44, 74, 26]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "OFR for Selected Time Period by Facility and Product (%)",
        "header": ["Facility", "bi", "cl", "cf", "cm"],
        "data": [[3, 3, 4, 5, 3], [2, 2, 2, 4, 1], [4, 4, 4, 4, 6]],
        "cell_width": "135px",
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

    ret_obj['table1'] = table1
    ret_obj['table2'] = table2
    ret_obj['line'] = line_chart
    return ret_obj

def rsqr_context():
    ret_obj = {}

    table = {
        "title": "All Products (Aggregated Quantity required to ensure that HC can resupply",
        "header": ["Facility Name", "%HSA with Stockout", "LA 1x6", "LA 2x6", "Zinc"],
        "data": [['BULA', 32, 4123, 512, 3123], ['Chesamu', 22, 2123, 423, 123], ['Chikwina', 45, 4123, 423, 612]],
        "cell_width": "135px",
    }

    ret_obj['table'] = table
    return ret_obj

def as_context():
    ret_obj = {}

    table = {
        "title": "Current Alert Summary",
        "header": ["Facility", "# HSA", "%HSA stocked out", "%HSA with EO", "%HSA with no Products"],
        "data": [['BULA', 332, 42, 53, 35], ['Chesamu', 232, 25, 41, 11], ['Chikwina', 443, 41, 41, 46]],
        "cell_width": "135px",
    }
    
    ret_obj['table'] = table
    return ret_obj

def cp_context():
    ret_obj = {}

    table1 = {
        "title": "District Consumption Profiles",
        "header": ["Product", "Total Calc Cons", "Av Rep Rate", "AMC", "Total SOH"],
        "data": [['cc', 312, "47%", 5, 354], ['dt', 1322, "21%", 4, 121], ['sr', 4123, "14%", 4, 634]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "Facility Consumption Profiles",
        "header": ["Product", "Total Calc Cons", "Av Rep Rate", "AMC", "Total SOH"],
        "data": [['cc', 3234, "40%", 5, 345], ['dt', 2123, "52%", 4, 111], ['sr', 4132, "43%", 4, 634]],
        "cell_width": "135px",
    }

    line_chart = {
        "height": "350px",
        "width": "100%", # "300px",
        "series": [],
    }
    for j in ['Av Monthly Cons', 'Av Months of Stock']:
        temp = []
        for i in range(0,5):
            temp.append([random(),random()])
        line_chart["series"].append({"title": j, "data": sorted(temp)})

    ret_obj['table1'] = table1
    ret_obj['table2'] = table2
    ret_obj['line'] = line_chart
    return ret_obj

def ss_context():
    ret_obj = {}
    summary = {
        "product_codes": [],
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
    
    count = 0
    for product in Product.objects.all().order_by('sms_code')[0:10]:
        count += 1
        summary['product_codes'].append([count, '<span>%s</span>' % (str(product.code.lower()))])
        summary['xlabels'] = summary['product_codes']
    
    summary['data'] = barseries(['Stocked Out','Under Stock','Adequate'], 10)

    table1 = {
        "title": "",
        "header": ["Product", "HSA Stocked Out", "HSA Under", "HSA Adequate", "Overstock"],
        "data": [['cc', 34, 45, 52, 31], ['dt', 21, 25, 44, 17], ['sr', 43, 44, 41, 67]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "HSA Current Stock Status by District",
        "header": ["District", "HSA Stocked Out", "HSA Under", "HSA Adequate", "Overstock"],
        "data": [['cc', 33, 45, 52, 31], ['dt', 21, 29, 45, 13], ['sr', 43, 42, 42, 61]],
        "cell_width": "135px",
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

    ret_obj['summary'] = summary
    ret_obj['table1'] = table1
    ret_obj['table2'] = table2
    ret_obj['line'] = line_chart
    return ret_obj

def rr_context():
    ret_obj = {}
    summary = {
        "product_codes": [],
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
    
    count = 0
    xlabels = ['Jun', 'July', 'Aug']
    for xlabel in xlabels:
        count += 1
        summary['xlabels'].append([count, '<span>%s</span>' % str(xlabel)])
    
    summary['data'] = barseries(['on_time','late','not_reported'], len(xlabels))

    table1 = {
        "title": "",
        "header": ["Months", "%Reporting", "%Ontime", "%Late", "%None"],
        "data": [['June', 10, 47, 55, 31], ['July', 50, 24, 43, 15], ['Aug', 40, 47, 45, 61]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "Average Reporting Rate (Districts)",
        "header": ["Districts", "%Reporting", "%Ontime", "%Late", "%None"],
        "data": [['All', 32, 41, 54, 36], ['Nkatabay', 27, 27, 44, 11], ['Kasungu', 45, 44, 44, 67]],
        "cell_width": "135px",
    }

    table3 = {
        "title": "Average Reporting Rate (Facilities)",
        "header": ["Facilities", "%Reporting", "%Ontime", "%Late", "%None"],
        "data": [['All', 34, 45, 56, 38], ['Chesamu', 24, 22, 47, 18], ['Chikwina', 44, 44, 42, 65]],
        "cell_width": "135px",
    }

    ret_obj['summary'] = summary
    ret_obj['table1'] = table1
    ret_obj['table2'] = table2
    ret_obj['table3'] = table3
    return ret_obj

def hsas(request):
    context = {}
    return render_to_response('malawi/new/hsas.html', context, context_instance=RequestContext(request))

def user_profiles(request):
    context = {}
    return render_to_response('malawi/new/user-profiles.html', context, context_instance=RequestContext(request))

def _get_window_date(request=None):
    # TODO: this should actually come from the request, but this is hard-coded
    # for testing, 
    return datetime(2012, 6, 1) # temp for testing

def _pct(num, denom):
    return float(num) / (float(denom) or 1) * 100
