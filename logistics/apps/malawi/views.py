from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from logistics.apps.malawi.tables import MalawiContactTable, MalawiLocationTable, \
    MalawiProductTable, HSATable, StockRequestTable, \
    HSAStockRequestTable, DistrictTable
from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
from logistics.apps.logistics.models import SupplyPoint, Product, \
    StockTransaction, StockRequestStatus, StockRequest
from logistics.apps.malawi.util import get_districts, get_facilities, hsas_below
from logistics.apps.logistics.decorators import place_in_request
from logistics.apps.logistics.charts import stocklevel_plot
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from logistics.apps.logistics.view_decorators import filter_context
from logistics.apps.logistics.reports import ReportingBreakdown
from logistics.apps.logistics.util import config

@place_in_request()
def dashboard(request, days=30):
    base_facilites = SupplyPoint.objects.filter(type__code="hsa")
    
    # district filter
    if request.location:
        valid_facilities = get_facilities().filter(parent_id=request.location.pk)
        base_facilites = base_facilites.filter(location__parent_id__in=[f.pk for f in valid_facilities])
    
    # reporting info
    report = ReportingBreakdown(base_facilites, days)
    return render_to_response("malawi/dashboard.html",
                              {"reporting_data": report,
                               "hsas_table": MalawiContactTable(Contact.objects.filter(role__code="hsa"), request=request),
                               "graph_width": 200,
                               "graph_height": 200,
                               "districts": get_districts().order_by("code"),
                               "location": request.location,
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
    
@filter_context
def facility(request, code, context={}):
    facility = get_object_or_404(SupplyPoint, code=code)

    context["location"] = facility.location
    facility.location.supervisors = facility.contact_set.filter(is_active=True, role__code=config.Roles.HSA_SUPERVISOR)
    facility.location.in_charges = facility.contact_set.filter(is_active=True, role__code=config.Roles.IN_CHARGE)
    
    context["stockrequest_table"] = HSAStockRequestTable\
        (StockRequest.objects.filter(supply_point__supplied_by=facility)\
                             .exclude(status=StockRequestStatus.CANCELED), request)
    
    
    return render_to_response("malawi/single_facility.html",
        context, context_instance=RequestContext(request))
    
