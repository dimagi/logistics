


'''
New views for the upgraded reports of the system.
'''
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect
from django.utils.datastructures import SortedDict

from logistics.models import Product

from logistics_project.apps.malawi.util import get_facilities, get_districts

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
    
def get_report(request, slug=''):
    context = shared_context(request)
    context.update({"report_list": stub_reports,
                    "slug": slug})
    return render_to_response("malawi/new/%s.html" % slug, 
                              context,
                              context_instance=RequestContext(request))

def shared_context(request):
    return { "districts": get_districts(),
             "facilities": get_facilities(),
             "hsas": 643,
             "reporting_rate": "93.3",
             "products": Product.objects.all().order_by('sms_code')
    }