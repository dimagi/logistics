from django.shortcuts import render_to_response
from django.template.context import RequestContext
from logistics.apps.malawi.tables import MalawiContactTable, MalawiLocationTable
from logistics.apps.registration.tables import ContactTable
from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location


def dashboard(request):
    return render_to_response("malawi/dashboard.html", {}, 
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
    