from django.shortcuts import render_to_response
from django.template.context import RequestContext
from logistics.apps.malawi.tables import MalawiContactTable
from logistics.apps.registration.tables import ContactTable
from rapidsms.models import Contact


def dashboard(request):
    return render_to_response("malawi/dashboard.html", {}, 
                              context_instance=RequestContext(request))

def contacts(request):
    return render_to_response("malawi/contacts.html",
        {
            "contacts_table": MalawiContactTable(Contact.objects, request=request)
        }, context_instance=RequestContext(request)
    )
    