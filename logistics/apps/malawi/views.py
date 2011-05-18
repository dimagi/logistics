from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from logistics.apps.malawi.tables import MalawiContactTable, MalawiLocationTable,\
    MalawiProductTable, HSATable
from logistics.apps.registration.tables import ContactTable
from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
from logistics.apps.logistics.models import SupplyPoint, Product
from datetime import datetime, timedelta
from django.db.models.query_utils import Q


def dashboard(request, days=30):
    since  = datetime.utcnow() - timedelta(days=days)
    base_facilites = SupplyPoint.objects.filter(type__code="hsa")
    late_facilities = base_facilites.filter(Q(last_reported__lt=since) | Q(last_reported=None)).order_by('-last_reported','name')
    on_time_facilities = base_facilites.filter(last_reported__gte=since).order_by('-last_reported','name')
    
    return render_to_response("malawi/dashboard.html", 
                              {"late_facilities": late_facilities,
                               "on_time_facilities": on_time_facilities,
                               "hsas_table": MalawiContactTable(Contact.objects.filter(role__code="hsa"), request=request),
                               "graph_width": 200,
                               "graph_height": 200,
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

def hsas(request):
    location = None
    hsas = Contact.objects.filter(role__code="hsa")
    code = request.GET.get("place", None)
    
    if code:
        location = Location.objects.get(code=code)
        # support up to 3 levels of parentage. this covers
        # hsa->facility-> district, which is all we allow you to select
        hsas = hsas.filter(Q(supply_point__location=location) | \
                           Q(supply_point__supplied_by__location=location) | \
                           Q(supply_point__supplied_by__supplied_by__location=location))
    
    districts = Location.objects.filter(type__slug="district").order_by("id")
    facilities = Location.objects.filter(type__slug="facility").order_by("parent_id")
    
    hsa_table = HSATable(hsas, request=request)
    return render_to_response("malawi/hsas.html",
        {
            "hsas": hsas,
            "hsa_table": hsa_table,
            "location": location,
            "districts": districts,
            "facilities": facilities
        }, context_instance=RequestContext(request)
    )
    
def hsa(request, pk):
    hsa = get_object_or_404(Contact, pk=pk)
    return render_to_response("malawi/single_hsa.html",
        {
            "hsa": hsa
        }, context_instance=RequestContext(request)
    )
    
    
    
