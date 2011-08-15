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


@place_in_request()
def dashboard(request):
    
    base_facilities = SupplyPoint.objects.filter(active=True, type__code="hsa")
    em_group = None
    begin_date = None
    # district filter
    if request.location:
        valid_facilities = get_facilities().filter(parent_id=request.location.pk)
        base_facilities = base_facilities.filter(location__parent_id__in=[f.pk for f in valid_facilities])
        #em_group = (group_for_location(request.location) == config.Groups.EM)
    # reporting info
    report = ReportingBreakdown(base_facilities, DateSpan.since(30))#(group == config.Groups.EM))
    if em_group:
        begin_date = datetime.now().replace(day=1)
        end_date = datetime.now()
        d = DateSpan(begin_date, end_date)
        em_report = ReportingBreakdown(base_facilities, d, include_late = True, MNE=False)#(group == config.Groups.EM))
    else:
        em_report = None
    return render_to_response("tanzania/dashboard.html",
                              {"reporting_data": report,
#                               "hsas_table": MalawiContactTable(Contact.objects.filter(is_active=True,
#                                                                                       role__code="hsa"), request=request),
                               "graph_width": 200,
                               "graph_height": 200,
                               "em_group": em_group,
                               "em_report": em_report,
                               "begin_date": begin_date,
                               #"districts": get_districts().order_by("code"),
                               "location": request.location},
                               
                              context_instance=RequestContext(request))
PRODUCTS_PER_TABLE = 6

@login_required
@place_in_request
def facilities_detail(request):
    facs = SupplyPoint.objects.filter(type__code='facility', parent__location=request.location)
    products = Product.objects.all().order_by('name')
    products = chunks(products, PRODUCTS_PER_TABLE)
    return render_to_response("tanzania/facilities_list.html",
                              {'facs': facs,
                               'product_sets': products,
                               'location': request.location}, context_instance=RequestContext(request))

def facilities_index(request, view_type="inventory"):
    facs = SupplyPoint.objects.filter(type__code='facility')
    products = Product.objects.all().order_by('name')
    products = chunks(products, PRODUCTS_PER_TABLE)
    return render_to_response("tanzania/facilities_list.html",
                              {'facs': facs,
                               'product_set': products,
                               'view_type':view_type,
                               'location': None}, context_instance=RequestContext(request))

