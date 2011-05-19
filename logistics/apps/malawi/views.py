from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from logistics.apps.malawi.tables import MalawiContactTable, MalawiLocationTable,\
    MalawiProductTable, HSATable
from logistics.apps.registration.tables import ContactTable
from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
from logistics.apps.logistics.models import SupplyPoint, Product,\
    StockTransaction
from datetime import datetime, timedelta
from django.db.models.query_utils import Q
from logistics.apps.malawi.util import get_districts, get_facilities
from logistics.apps.logistics.decorators import place_in_request
from logistics.apps.logistics.charts import stocklevel_plot

@place_in_request()
def dashboard(request, days=30):
    since  = datetime.utcnow() - timedelta(days=days)
    base_facilites = SupplyPoint.objects.filter(type__code="hsa")
    late_facilities = base_facilites.filter(Q(last_reported__lt=since) | Q(last_reported=None)).order_by('-last_reported','name')
    on_time_facilities = base_facilites.filter(last_reported__gte=since).order_by('-last_reported','name')
    districts = get_districts().order_by("code")
    return render_to_response("malawi/dashboard.html", 
                              {"late_facilities": late_facilities,
                               "on_time_facilities": on_time_facilities,
                               "hsas_table": MalawiContactTable(Contact.objects.filter(role__code="hsa"), request=request),
                               "graph_width": 200,
                               "graph_height": 200,
                               "districts": districts,
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
    
def hsa(request, pk):
    hsa = get_object_or_404(Contact, pk=pk)
    transactions = StockTransaction.objects.filter(supply_point=hsa.supply_point)
    chart_data = stocklevel_plot(transactions) 
    
    return render_to_response("malawi/single_hsa.html",
        {
            "hsa": hsa,
            "chart_data": chart_data
        }, context_instance=RequestContext(request)
    )
    
    
    
