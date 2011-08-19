from logistics.decorators import place_in_request
from logistics.models import SupplyPoint, Product
from logistics.views import get_facilities
from logistics.reports import ReportingBreakdown
from dimagi.utils.dates import DateSpan
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from logistics_project.apps.malawi.util import facility_supply_points_below
from logistics_project.apps.tanzania.utils import chunks
from rapidsms.contrib.locations.models import Location
from dimagi.utils.decorators.datespan import datespan_in_request
from models import DeliveryGroups


@place_in_request()
def dashboard(request):
    month = request.GET.get('month', datetime.now().month)
    year = request.GET.get('month', datetime.now().year)
    
    base_facilities = SupplyPoint.objects.filter(active=True, type__code="facility")

    groups = DeliveryGroups.facilities_by_group()
    
    em_group = None
    begin_date = None
    # district filter
    if request.location:
        location = request.location
        valid_facilities = get_facilities().filter(parent_id=location.pk)
        base_facilities = base_facilities.filter(location__parent_id__in=[f.pk for f in valid_facilities])
    else:
        location = Location.objects.get(name="MOHSW")
#    report = ReportingBreakdown(base_facilities, DateSpan.since(30))#(group == config.Groups.EM))
    return render_to_response("tanzania/dashboard.html",
                              {
                               "graph_width": 200,
                               "graph_height": 200,
                               "dg_model": DeliveryGroups,
                               "groups": groups,
                               "facilities": list(base_facilities),
                               "begin_date": begin_date,
                               "location": location},
                               
                              context_instance=RequestContext(request))
PRODUCTS_PER_TABLE = 6

#@login_required
@place_in_request
@datespan_in_request()
def facilities_detail(request, view_type="inventory"):
    facs = SupplyPoint.objects.filter(type__code='facility', parent__location=request.location)
    products = Product.objects.all().order_by('name')
    products = chunks(products, PRODUCTS_PER_TABLE)
    return render_to_response("tanzania/facilities_list.html",
                              {'facs': facs,
                               'product_sets': products,
                               'location': request.location}, context_instance=RequestContext(request))

def datespan_to_month(datespan):
    return datespan.startdate.month

#@login_required
@datespan_in_request()
def facilities_index(request, view_type="inventory"):
    facs = SupplyPoint.objects.filter(type__code='facility')
    products = Product.objects.all().order_by('name')
    products = chunks(products, PRODUCTS_PER_TABLE)
    return render_to_response("tanzania/facilities_list.html",
                              {'facs': facs,
                               'product_set': products,
                               'location': None,
                               'begin_date': request.datespan.startdate if request.datespan else datetime.utcnow().replace(day=1),
                               'end_date': request.datespan.enddate if request.datespan else datetime.utcnow()
                               }, context_instance=RequestContext(request))


def facilities_ordering(request):
    pass
