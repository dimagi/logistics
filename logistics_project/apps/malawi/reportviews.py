


'''
New views for the upgraded reports of the system.
'''
from django.template.context import RequestContext
from django.shortcuts import render_to_response
from logistics_project.apps.malawi.util import get_facilities, get_districts
from logistics.models import Product

REPORT_LIST = [
    "Dashboard",
    "Reporting Rate",
    "Stock Status",
    "Consumption Profiles",
    "Alert Summary",
    "Re-supply Qts Required",
    "Lead Times",
    "Order Fill Rate",
    "Emergency Orders"
]

to_stub = lambda x: {"slug": x, "name": x}

stub_reports = [to_stub(r) for r in REPORT_LIST]

def home(request):
    context = shared_context(request)
    context.update({"report_list": stub_reports,
                    "slug": "Dashboard"})
    return render_to_response("malawi/new/dashboard.html", 
                              context,
                              context_instance=RequestContext(request))
    
def shared_context(request):
    return { "districts": get_districts(),
             "facilities": get_facilities(),
             "hsas": 643,
             "reporting_rate": "93.3",
             "products": Product.objects.all().order_by('sms_code')
    }