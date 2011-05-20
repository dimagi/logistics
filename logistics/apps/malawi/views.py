from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from logistics.apps.malawi.tables import MalawiContactTable, MalawiLocationTable,\
    MalawiProductTable, HSATable, StockRequestTable, FacilityTable
from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
from logistics.apps.logistics.models import SupplyPoint, Product,\
    StockTransaction, ProductReport
from datetime import datetime, timedelta
from django.db.models.query_utils import Q
from logistics.apps.malawi.util import get_districts, get_facilities,\
    get_facility_supply_points
from logistics.apps.logistics.decorators import place_in_request
from logistics.apps.logistics.charts import stocklevel_plot
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from logistics.apps.logistics.view_decorators import filter_context
from logistics.apps.logistics.const import Reports

@place_in_request()
def dashboard(request, days=30):
    since  = datetime.utcnow() - timedelta(days=days)
    base_facilites = SupplyPoint.objects.filter(type__code="hsa")
    
    # district filter
    if request.location:
        valid_facilities = get_facilities().filter(parent_id=request.location.pk)
        base_facilites = base_facilites.filter(location__parent_id__in=[f.pk for f in valid_facilities])
    
    # reporting info
    late_hsas = base_facilites.filter(Q(last_reported__lt=since) | Q(last_reported=None)).order_by('-last_reported','name')
    on_time_hsas = base_facilites.filter(last_reported__gte=since).order_by('-last_reported','name')
    
    # fully reporting / non reporting
    full = partial = unconfigured = 0
    for hsa_sp in on_time_hsas.all():
        hsa = Contact.objects.get(supply_point=hsa_sp)
        found_reports = ProductReport.objects.filter(supply_point=hsa_sp, 
                                                     report_type__code=Reports.SOH,
                                                     report_date__gte=since)
        found_products = set(found_reports.values_list("product", flat=True))
        needed_products = set([c.pk for c in hsa.commodities.all()])
        if needed_products:
            if needed_products - found_products:
                partial = partial + 1 
            else:
                full = full + 1
        else:
            unconfigured = unconfigured + 1
    graph_data = [
        {"display": "Fully Reported",
         "value": full,
         "color": "green",
         "description": "%s in last %s days" % ("Fully reported", days)
        },
        {"display": "Partially Reported",
         "value": partial,
         "color": "purple",
         "description": "%s in last %s days" % ("Partially reported", days)
        },
        {"display": "Unconfigured",
         "value": unconfigured,
         "color": "red",
         "description": "Unconfigured for stock information"
        }
    ]     

    return render_to_response("malawi/dashboard.html", 
                              {"late_facilities": late_hsas,
                               "on_time_facilities": on_time_hsas,
                               "hsas_table": MalawiContactTable(Contact.objects.filter(role__code="hsa"), request=request),
                               "graph_width": 200,
                               "graph_height": 200,
                               "districts": get_districts().order_by("code"),
                               "location": request.location,
                               "reporting_details": graph_data,
                               "days": days}, 
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
    hsas = Contact.objects.filter(role__code="hsa")
    
    if request.location:
        # support up to 3 levels of parentage. this covers
        # hsa->facility-> district, which is all we allow you to select
        hsas = hsas.filter(Q(supply_point__location=request.location) | \
                           Q(supply_point__supplied_by__location=request.location) | \
                           Q(supply_point__supplied_by__supplied_by__location=request.location))
    
    
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
    transactions = StockTransaction.objects.filter(supply_point=hsa.supply_point)
    chart_data = stocklevel_plot(transactions) 
    
    stockrequest_table = StockRequestTable(hsa.supply_point.stockrequest_set, request)
    return render_to_response("malawi/single_hsa.html",
        {
            "hsa": hsa,
            "chart_data": chart_data,
            "stockrequest_table": stockrequest_table 
        }, context_instance=RequestContext(request)
    )
    
@place_in_request()
def facilities(request):
    facilities = get_facilities().order_by("parent_id", "code")
    
    if request.location:
        if request.location.type.slug == "district":
            display_facilities = facilities.filter(parent_id=request.location.id)
        else:
            assert(request.location.type.slug == "facility")
            return HttpResponseRedirect(reverse("malawi_facility", args=[request.location.code]))
    else:
        display_facilities = facilities
    
    return render_to_response("malawi/facilities.html",
        {
            "location": request.location,
            "facilities": facilities,
            "facilities_table": FacilityTable(display_facilities, request=request),
            "districts": get_districts().order_by("id")
        }, context_instance=RequestContext(request))
    
@filter_context
def facility(request, code, context={}):
    facility = get_object_or_404(SupplyPoint, code=code)

    context["location"] = facility.location
    return render_to_response("malawi/single_facility.html",
        context, context_instance=RequestContext(request))
    
