'''
New views for the upgraded reports of the system.
'''
from random import random
from datetime import datetime, timedelta

from django.conf import settings
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect
from django.utils.datastructures import SortedDict

from logistics.models import Product

from logistics_project.apps.malawi.util import get_facilities, get_districts
from dimagi.utils.decorators.datespan import datespan_in_request
from rapidsms.contrib.locations.models import Location
from dimagi.utils.dates import months_between

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
    
@datespan_in_request()
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
        'lead-times': leadtimes_context,
    }
    if slug in func_map:
        return func_map[slug]()
    else:
        return {}


def shared_context(request):
    return { "settings": settings,
             "location": None,
             "districts": get_districts(),
             "facilities": get_facilities(),
             "hsas": 643,
             "reporting_rate": "93.3",
             "products": Product.objects.all().order_by('sms_code')
    }

def timechart(labels):
    summary = {
        "xlabels": [],
        "legenddiv": "legend-div",
        "div": "chart-div",
        "max_value": 3,
        "width": "730px",
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


def leadtimes_context():
    table = {
        "title": "",
        "header": ['Month', 'Ord-Ord Ready (days)', 'Ord-Ord Received(days)', 'Total Lead Time (days)'],
        "data": [['Jan', 3, 14, 7], ['Feb', 12, 7, 4], ['Mar', 14, 6, 4]],
    }
    return {"summary": timechart(['Ord-Ord Ready', 'Ord-Ord Received']),
            "month_table": table}

def dashboard_context():
    return {"summary": timechart(['on time','late','not reported'])}

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
        "title": "Exhibit A",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 3, 4, 5, 3], ['dt', 2, 2, 4, 1], ['sr', 4, 4, 4, 6]],
        "cell_width": "135px",
    }

    line_chart = {
        "height": "350px",
        "width": "100%", # "300px",
        "series": [],
    }
    for j in ['before', 'after']:
        temp = []
        for i in range(0,5):
            temp.append([random(),random()])
        line_chart["series"].append({"title": j, "data": temp})

    ret_obj['summary'] = summary
    ret_obj['table'] = table
    ret_obj['line'] = line_chart
    return ret_obj


def ofr_context():
    ret_obj = {}

    table1 = {
        "title": "Exhibit A",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 3, 4, 5, 3], ['dt', 2, 2, 4, 1], ['sr', 4, 4, 4, 6]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "Exhibit A",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 3, 4, 5, 3], ['dt', 2, 2, 4, 1], ['sr', 4, 4, 4, 6]],
        "cell_width": "135px",
    }

    line_chart = {
        "height": "350px",
        "width": "100%", # "300px",
        "series": [],
    }
    for j in ['before', 'after']:
        temp = []
        for i in range(0,5):
            temp.append([random(),random()])
        line_chart["series"].append({"title": j, "data": temp})

    ret_obj['table1'] = table1
    ret_obj['table2'] = table2
    ret_obj['line'] = line_chart
    return ret_obj

def rsqr_context():
    ret_obj = {}

    table = {
        "title": "Exhibit A",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 3, 4, 5, 3], ['dt', 2, 2, 4, 1], ['sr', 4, 4, 4, 6]],
        "cell_width": "135px",
    }

    ret_obj['table'] = table
    return ret_obj

def as_context():
    ret_obj = {}

    table = {
        "title": "Exhibit A",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 3, 4, 5, 3], ['dt', 2, 2, 4, 1], ['sr', 4, 4, 4, 6]],
        "cell_width": "135px",
    }
    
    ret_obj['table'] = table
    return ret_obj

def cp_context():
    ret_obj = {}

    table1 = {
        "title": "Exhibit A",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 3, 4, 5, 3], ['dt', 2, 2, 4, 1], ['sr', 4, 4, 4, 6]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "Exhibit A",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 3, 4, 5, 3], ['dt', 2, 2, 4, 1], ['sr', 4, 4, 4, 6]],
        "cell_width": "135px",
    }

    line_chart = {
        "height": "350px",
        "width": "100%", # "300px",
        "series": [],
    }
    for j in ['before', 'after']:
        temp = []
        for i in range(0,5):
            temp.append([random(),random()])
        line_chart["series"].append({"title": j, "data": temp})

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
    
    summary['data'] = barseries(['a','b','c'], 10)

    table1 = {
        "title": "Exhibit A",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 3, 4, 5, 3], ['dt', 2, 2, 4, 1], ['sr', 4, 4, 4, 6]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "Exhibit A",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 3, 4, 5, 3], ['dt', 2, 2, 4, 1], ['sr', 4, 4, 4, 6]],
        "cell_width": "135px",
    }

    line_chart = {
        "height": "350px",
        "width": "100%", # "300px",
        "series": [],
    }
    for j in ['before', 'after']:
        temp = []
        for i in range(0,5):
            temp.append([random(),random()])
        line_chart["series"].append({"title": j, "data": temp})

    ret_obj['summary'] = summary
    ret_obj['table1'] = table1
    ret_obj['table2'] = table2
    ret_obj['line'] = line_chart
    return ret_obj

def lt_context():
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

    table1 = {
        "title": "Exhibit A",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 3, 4, 5, 3], ['dt', 2, 2, 4, 1], ['sr', 4, 4, 4, 6]],
        "cell_width": "135px",
    }

    table2 = {
        "title": "Exhibit A",
        "header": ["Product", "Jan", "Feb", "Mar", "Apr"],
        "data": [['cc', 3, 4, 5, 3], ['dt', 2, 2, 4, 1], ['sr', 4, 4, 4, 6]],
        "cell_width": "135px",
    }

    ret_obj['summary'] = summary
    ret_obj['table1'] = table1
    ret_obj['table2'] = table2
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
