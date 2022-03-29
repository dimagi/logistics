from __future__ import absolute_import
from __future__ import unicode_literals
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from rapidsms.contrib.messaging.utils import send_message
from rapidsms.models import Contact
from logistics.models import ContactRole
from logistics_project.apps.registration.forms import ContactForm
from static.malawi.config import Roles
from .tables import ContactTable


@permission_required('rapidsms.add_contact')
def registration(req, pk=None, template="registration/dashboard.html"):
    contact = None
    registration_view = 'registration'

    if pk is not None:
        contact = get_object_or_404(
            Contact, pk=pk)
            
    if req.method == "POST":
        if req.POST["submit"] == "Delete Contact":
            contact.delete()
            return HttpResponseRedirect(
                reverse(registration_view))

        else:
            contact_form = ContactForm(
                instance=contact,
                data=req.POST)

            if contact_form.is_valid():
                created = False
                if contact is None:
                    created = True
                contact = contact_form.save()
                if created:
                    response = "Dear %(name)s, you have been registered on %(site)s" % \
                        {'name': contact.name, 
                         'site': Site.objects.get(id=settings.SITE_ID).domain }
                    send_message(contact.default_connection, response)
                    return HttpResponseRedirect(reverse(registration_view))

    else:
        contact_form = ContactForm(
            instance=contact)

    contacts_table = ContactTable(Contact.objects.all(), request=req)
    search_term = req.GET.get('search_term')
    if search_term:
        search_term_lower = search_term.lower()
        search_term_upper = search_term.upper()
        search_term_proper = search_term[0].upper() + search_term[1:]
        contacts_table = ContactTable(Contact.objects.filter(Q(name__contains=search_term) |
                                                             Q(name__contains=search_term_lower) |
                                                             Q(name__contains=search_term_upper) |
                                                             Q(name__contains=search_term_proper)),
                                                             request=req)

    return render(req, template, {
            "contacts_table": contacts_table,
            "contact_form": contact_form,
            "contact": contact,
            "hsa_role_id": ContactRole.objects.get(code=Roles.HSA).pk,
            "registration_view": reverse(registration_view)
        },
    )


def search(req):
    return redirect('/registration/?search_term=%s' % (req.POST.get('search_term')))
