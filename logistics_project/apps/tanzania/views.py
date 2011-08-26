from logistics.decorators import place_in_request
from logistics.models import SupplyPoint, Product
from django.db.models.query_utils import Q
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.utils import translation
from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown
from logistics_project.apps.tanzania.tables import OrderingStatusTable
from logistics_project.apps.tanzania.utils import chunks
from rapidsms.contrib.locations.models import Location
from models import DeliveryGroups
from logistics.views import MonthPager
from django.core.urlresolvers import reverse
from django.conf import settings
from logistics_project.apps.tanzania.decorators import gdata_required
import gdata.docs.client
import gdata.gauth
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from dimagi.utils.parsing import string_to_datetime

def tz_location_url(location):
    try:
        sp = SupplyPoint.objects.get(location=location)
        if sp.type.code == "facility":
            return reverse("tz_facility_details", args=(sp.pk,))
    except SupplyPoint.DoesNotExist:
        pass
    return ""

def _get_facilities_and_location(request):
    base_facilities = SupplyPoint.objects.filter(active=True, type__code="facility")

    # district filter
    if request.location:
        location = request.location
        print request.location, request.location.type.name
        if request.location.type.name == "REGION":
            print "Got a region"
            base_facilities = base_facilities.filter(Q(supplied_by__location__parent_id=location.id) | Q(supplied_by__location=location))
        elif request.location.type.name == "DISTRICT":
            base_facilities = base_facilities.filter(supplied_by__location=location)
    else:
        location = Location.objects.get(name="MOHSW")
    return base_facilities, location

def _districts():
    return Location.objects.filter(type__name="DISTRICT")
def _regions():
    return Location.objects.filter(type__name="REGION")

@place_in_request()
def dashboard(request):
    translation.activate("en")
    mp = MonthPager(request)
    base_facilities, location = _get_facilities_and_location(request)

    dg = DeliveryGroups(mp.month, facs=base_facilities)
    sub_data = SupplyPointStatusBreakdown(base_facilities, month=mp.month, year=mp.year)
    return render_to_response("tanzania/dashboard.html",
                              {
                               "sub_data": sub_data,
                               "graph_width": 300,
                               "graph_height": 300,
                               "dg": dg,
                               "month_pager": mp,
                               "facs": list(base_facilities), # Not named 'facilities' so it won't trigger the selector
                               "districts": _districts(),
                               "regions": _regions(),
                               "location": location},
                               
                              context_instance=RequestContext(request))
PRODUCTS_PER_TABLE = 6

#@login_required
@place_in_request()
def facilities_detail(request, view_type="inventory"):
    facs, location = _get_facilities_and_location(request)
    mp = MonthPager(reqyest)
    products = Product.objects.all().order_by('name')
    products = chunks(products, PRODUCTS_PER_TABLE)
    return render_to_response("tanzania/facilities_list.html",
                              {'facs': facs,
                               'product_sets': products,
                               'month_pager': mp,
                               'districts': _districts(),
                               "regions": _regions(),
                               'location': location}, context_instance=RequestContext(request))

def datespan_to_month(datespan):
    return datespan.startdate.month

#@login_required
@place_in_request()
def facilities_index(request, view_type="inventory"):
    # TODO Needs ability to view stock as of a given month.
    facs, location = _get_facilities_and_location(request)
    mp = MonthPager(request)
    products = Product.objects.all().order_by('name')
    products = chunks(products, PRODUCTS_PER_TABLE)
    return render_to_response("tanzania/facilities_list.html",
                              {'facs': facs,
                               'product_set': products,
                               'location': location,
                               'month_pager': mp,
                               'districts': _districts(),
                               "regions": _regions(),
                               }, context_instance=RequestContext(request))
@place_in_request()
def facilities_ordering(request):
    facs, location = _get_facilities_and_location(request)
    mp = MonthPager(request)
    return render_to_response(
        "tanzania/facilities_ordering.html",
        {
            "month_pager": mp,
            "districts": _districts(),
            "regions": _regions(),
            "location": location,
            "table": OrderingStatusTable(object_list=facs, request=request, month=mp.month, year=mp.year)
        },
        context_instance=RequestContext(request))

def facility_details(request, facility_id):
    facility = get_object_or_404(SupplyPoint, pk=facility_id)
    return render_to_response(
        "tanzania/facility_details.html",
        {
            "facility": facility,
            "report_types": ['Stock on Hand', 'Months of Stock']
        },
        context_instance=RequestContext(request))

@gdata_required
def docdownload(request, facility_id):
    """
    Download google docs document
    """
    if 'token' in request.session:
        #should be able to make this global
        client = gdata.docs.client.DocsClient()
        client.ssl = True  # Force all API requests through HTTPS
        client.http_client.debug = False  # Set to True for debugging HTTP requests
        client.auth_token = gdata.gauth.AuthSubToken(request.session['token'])
        supply_point = get_object_or_404(SupplyPoint, pk=facility_id)
        query_string = '/feeds/default/private/full?title=%s&title-exact=false&max-results=100' % supply_point.code
        feed = client.GetDocList(uri=query_string)

        most_recent_doc = None

        if not feed.entry:
            messages.error(request, 'Sorry, there is no recent R&R for this facility.')
            return HttpResponseRedirect(reverse("tz_facility_details", args=[supply_point.pk]))
        else:
            for entry in feed.entry:
                if not most_recent_doc:
                    most_recent_doc = entry
                else:
                    new_date = string_to_datetime(entry.updated.text)
                    old_date = string_to_datetime(most_recent_doc.updated.text)
                    if new_date > old_date:
                        most_recent_doc = entry

        exportFormat = '&exportFormat=pdf'
        content = client.GetFileContent(uri=most_recent_doc.content.src + exportFormat)
    
    response = HttpResponse(content)
    response['content-Type'] = 'application/pdf'
    response['Content-Disposition'] = 'inline; filename=%s' % most_recent_doc.title.text
    return response

def change_language(request):
    language = dict(settings.LANGUAGES)[request.LANGUAGE_CODE]   
    return render_to_response('tanzania/change_language.html',
                              {'LANGUAGES': settings.LANGUAGES,
                               "language": language},
                              context_instance=RequestContext(request))

