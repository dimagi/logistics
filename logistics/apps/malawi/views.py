from datetime import datetime, date
from django.core.serializers import json
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from urllib import urlencode
from urllib2 import urlopen
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
import logging
from logistics.apps.malawi.tables import MalawiContactTable, MalawiLocationTable, \
    MalawiProductTable, HSATable, StockRequestTable, \
    HSAStockRequestTable, DistrictTable
from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
from logistics.apps.logistics.models import SupplyPoint, Product, \
    StockTransaction, StockRequestStatus, StockRequest, ProductReport
from logistics.apps.malawi.util import get_districts, get_facilities, hsas_below, group_for_location
from logistics.apps.logistics.decorators import place_in_request
from logistics.apps.logistics.charts import stocklevel_plot
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from logistics.apps.logistics.view_decorators import filter_context
from logistics.apps.logistics.reports import ReportingBreakdown
from logistics.apps.logistics.util import config
from dimagi.utils.dates import DateSpan
from dimagi.utils.decorators.datespan import datespan_in_request
from django.contrib.auth.decorators import permission_required
from logistics.apps.malawi.reports import ReportInstance, ReportDefinition,\
    REPORT_SLUGS, REPORTS_CURRENT, REPORTS_LOCATION

from static.malawi.scmgr_const import PRODUCT_CODE_MAP, HEALTH_FACILITY_MAP
from django.conf import settings

@cache_page(60 * 15)
@place_in_request()
def dashboard(request):
    
    base_facilities = SupplyPoint.objects.filter(active=True, type__code="hsa")
    group = None
    # district filter
    if request.location:
        valid_facilities = get_facilities().filter(parent_id=request.location.pk)
        base_facilities = base_facilities.filter(location__parent_id__in=[f.pk for f in valid_facilities])
        group = group_for_location(request.location)
    # reporting info
    report = ReportingBreakdown(base_facilities, DateSpan.since(30), include_late = False, MNE=False)#(group == config.Groups.EM))
    return render_to_response("malawi/dashboard.html",
                              {"reporting_data": report,
                               "hsas_table": MalawiContactTable(Contact.objects.filter(is_active=True,
                                                                                       role__code="hsa"), request=request),
                               "graph_width": 200,
                               "graph_height": 200,
                               "districts": get_districts().order_by("code"),
                               "location": request.location},
                               
                              context_instance=RequestContext(request))

def places(request):
    return render_to_response("malawi/places.html",
        {
            "location_table": MalawiLocationTable(Location.objects.exclude(type__slug="hsa"), request=request)
        }, context_instance=RequestContext(request)
    )
    
def contacts(request):
    return render_to_response("malawi/contacts.html",
        {
            "contacts_table": MalawiContactTable(Contact.objects, request=request)
        }, context_instance=RequestContext(request)
    )
    
def products(request):
    return render_to_response("malawi/products.html",
        {
            "product_table": MalawiProductTable(Product.objects, request=request)
        }, context_instance=RequestContext(request)
    )

@place_in_request()
def hsas(request):
    hsas = hsas_below(request.location)
    districts = get_districts().order_by("id")
    facilities = get_facilities().order_by("parent_id")
    
    hsa_table = HSATable(hsas, request=request)
    return render_to_response("malawi/hsas.html",
        {
            "hsas": hsas,
            "hsa_table": hsa_table,
            "location": request.location,
            "districts": districts,
            "facilities": facilities
        }, context_instance=RequestContext(request)
    )
    
def hsa(request, code):
    hsa = get_object_or_404(Contact, supply_point__code=code)
    assert(hsa.supply_point.type.code == config.SupplyPointCodes.HSA)
    
    transactions = StockTransaction.objects.filter(supply_point=hsa.supply_point)
    chart_data = stocklevel_plot(transactions) 
    
    stockrequest_table = StockRequestTable(hsa.supply_point.stockrequest_set\
                                           .exclude(status=StockRequestStatus.CANCELED), request)
    return render_to_response("malawi/single_hsa.html",
        {
            "hsa": hsa,
            "chart_data": chart_data,
            "stockrequest_table": stockrequest_table 
        }, context_instance=RequestContext(request)
    )

@cache_page(60 * 15)
@place_in_request()
def facilities(request):
    facilities = get_facilities().order_by("parent_id", "code")
    
    if request.location:
        if request.location.type.slug == "district":
            table = None # nothing to do, handled by aggregate
        else:
            assert(request.location.type.slug == "facility")
            return HttpResponseRedirect(reverse("malawi_facility", args=[request.location.code]))
    else:
        table = DistrictTable(get_districts(), request=request)
    return render_to_response("malawi/facilities.html",
        {
            "location": request.location,
            "facilities": facilities,
            "table": table,
            "districts": get_districts().order_by("code")
        }, context_instance=RequestContext(request))

@cache_page(60 * 15)
@filter_context
@datespan_in_request()
def facility(request, code, context={}):
    facility = get_object_or_404(SupplyPoint, code=code)
    assert(facility.type.code == config.SupplyPointCodes.FACILITY)
    context["location"] = facility.location
    facility.location.supervisors = facility.contact_set.filter\
        (is_active=True, role__code=config.Roles.HSA_SUPERVISOR)
    facility.location.in_charges = facility.contact_set.filter\
        (is_active=True, role__code=config.Roles.IN_CHARGE)
    
    context["stockrequest_table"] = HSAStockRequestTable\
        (StockRequest.objects.filter(supply_point__supplied_by=facility,
                                     requested_on__gte=request.datespan.startdate, 
                                     requested_on__lte=request.datespan.enddate)\
                             .exclude(status=StockRequestStatus.CANCELED), request)
    
    
    return render_to_response("malawi/single_facility.html",
        context, context_instance=RequestContext(request))
    
@permission_required("is_superuser")
def monitoring(request):
    reports = (ReportDefinition(slug) for slug in REPORT_SLUGS) 
    return render_to_response("malawi/monitoring_home.html", {"reports": reports},
                              context_instance=RequestContext(request))
@cache_page(60 * 15)
@permission_required("is_superuser")
@datespan_in_request()
def monitoring_report(request, report_slug):
    report_def = ReportDefinition(report_slug)
    if report_slug in REPORTS_CURRENT: request.datespan = "current"
    if report_slug in REPORTS_LOCATION:
        request.select_location=True
        code = request.GET.get("place", None)
        if code:
            request.location = Location.objects.get(code=code)
        else:
            request.location = None
        location = request.location
        instance = ReportInstance(report_def, request.datespan, request.location)
        facilities = get_facilities().order_by("parent_id", "code")
    else:
        instance = ReportInstance(report_def, request.datespan)
        facilities = None
        location = None
    return render_to_response("malawi/monitoring_report.html",
                              {"report": instance,
                               "facilities": facilities,
                               "location": location},
                              context_instance=RequestContext(request))

def monitoring_report_ajax(): pass

def help(request):
    return render_to_response("malawi/help.html", {}, context_instance=RequestContext(request))

@permission_required("is_superuser")
def status(request):
    #TODO Put these settings in localsettings, probably
    f = urlopen(settings.KANNEL_URL)
    r = f.read()
    with open(settings.CELERY_HEARTBEAT_FILE) as f:
        r = "%s\n\nLast Celery Heartbeat:%s" % (r, f.read())
        
    return render_to_response("malawi/status.html", {'status': r}, context_instance=RequestContext(request))

def _sort_date(x,y):
    if x['registered'] < y['registered']: return -1
    if x['registered'] > y['registered']: return 1
    return 0

@permission_required("is_superuser")
def airtel_numbers(request):
    airtelcontacts = Contact.objects.select_related().filter(connection__backend__name='airtel-smpp')
    users = []
    for a in airtelcontacts:
        d = {
            'name': a.name,
            'phone': a.phone,
            'registered': a.message_set.all().order_by('-date')[0].date
        }
        users.append(d)
    users.sort(cmp=_sort_date, reverse=True)
    return render_to_response("malawi/airtel.html", {'users':users}, context_instance=RequestContext(request))

@csrf_exempt
def scmgr_receiver(request):
    if request.method != 'POST':
        return HttpResponse("You must submit POST data to this url.")
    data = request.POST.get('data', None)
    result = json.simplejson.loads(data)
    processed = 0
    for r in result:
        try:
            facility = SupplyPoint.objects.get(code=HEALTH_FACILITY_MAP[r[3]])
            pc = PRODUCT_CODE_MAP[r[6]].lower()
            product = Product.objects.get(sms_code=pc)
            date = datetime(year=r[4][0],month=r[4][1], day=1)
            if ProductReport.objects.filter(supply_point=facility, product=product, report_date=date).exists():
                # Server sent us some data we already have.  This means they should stop sending it.
                return HttpResponse('cStock SCMgr data fully updated.')
            quantity = r[0]
            is_stocked_out = r[2]
            if not quantity and not is_stocked_out:
                # If stock quantity is 0, but stockout not indicated, this line wasn't filled in.
                continue
            facility.report_stock(product, quantity, date=date)
            logging.info("SCMgr: Processed stock report %s %s %s %s" % (facility,product,quantity,date))
            processed += 1
        except (KeyError, SupplyPoint.DoesNotExist, Product.DoesNotExist) as e:
            # Server sent us some data we don't care about.  Keep on truckin'.
            continue
    if result:
        ret = "Processed %d entries." % processed
        return HttpResponse(ret, status=201) # Keep sending us stuff if you have more to send.
    else:
        ret = "Got no data -- ending update."
        return HttpResponse(ret)