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
        'emergency-orders': eo_context,
        'dashboard': dashboard_context
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

def barseries(labels, num_points):
    return [{"label": l, "data": bardata(num_points)} for l in labels]
    
def bardata(num_points):
    return [[i + 1, random()] for i in range(num_points)]


def dashboard_context():
    summary = {
        "xlabels": [],
        "legenddiv": "legend-div",
        "div": "chart-div",
        "max_value": 3,
        "width": 730,
        "height": 300,
        "data": [],
        "xaxistitle": "month",
        "yaxistitle": "rate"
    }
    count = 0
    for year, month in months_between(datetime.now() - timedelta(days=61), datetime.now()):
        count += 1
        summary['xlabels'].append([count, '<span>%s</span>' % datetime(year, month, 1).strftime("%b")])
        
    summary['data'] = barseries(['on time','late','not reported'], len(summary['xlabels']))
    return {"summary": summary}

    
def eo_context():
    ret_obj = {}
    summary = {
        "product_codes": [],
        "xlabels": [],
        "legenddiv": "legend-div",
        "div": "chart-div",
        "max_value": 3,
        "width": 400,
        "height": 200,
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
        "cell_width": "50px",
    }

    ret_obj['summary'] = summary
    ret_obj['table'] = table
    return ret_obj

