from django.shortcuts import render_to_response
from django.template.context import RequestContext
from logistics.apps.malawi.tables import MalawiContactTable, MalawiLocationTable
from logistics.apps.registration.tables import ContactTable
from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
from logistics.apps.logistics.models import SupplyPoint
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
    