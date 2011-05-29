#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf import settings
from django.template import RequestContext
from django.contrib.auth.decorators import permission_required
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.db import transaction
from django.shortcuts import render_to_response, get_object_or_404
from rapidsms.contrib.messaging.utils import send_message
from rapidsms.models import Connection
from rapidsms.models import Backend
from rapidsms.models import Contact
from logistics.apps.registration.forms import CommoditiesContactForm, BulkRegistrationForm
from .tables import ContactTable

@permission_required('rapidsms.add_contact')
def registration(req, pk=None, template="registration/dashboard.html"):
    contact = None
    connection = None
    bulk_form = None
    registration_view = 'registration'
    if hasattr(settings, 'SMS_REGISTRATION_VIEW'):
        registration_view = settings.SMS_REGISTRATION_VIEW

    if pk is not None:
        contact = get_object_or_404(
            Contact, pk=pk)
        try:
            connection = Connection.objects.get(contact=contact)
        except Connection.DoesNotExist:
            connection = None
            
    if req.method == "POST":
        if req.POST["submit"] == "Delete Contact":
            contact.delete()
            return HttpResponseRedirect(
                reverse(registration_view))

        elif "bulk" in req.FILES:
            # TODO use csv module
            #reader = csv.reader(open(req.FILES["bulk"].read(), "rb"))
            #for row in reader:
            for line in req.FILES["bulk"]:
                line_list = line.split(',')
                name = line_list[0].strip()
                backend_name = line_list[1].strip()
                identity = line_list[2].strip()

                contact = Contact(name=name)
                contact.save()
                # TODO deal with errors!
                backend = Backend.objects.get(name=backend_name)

                connection = Connection(backend=backend, identity=identity,\
                    contact=contact)
                connection.save()

            return HttpResponseRedirect(
                reverse(registration_view))
        else:
            contact_form = CommoditiesContactForm(
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
        contact_form = CommoditiesContactForm(
            instance=contact)
        bulk_form = BulkRegistrationForm()
    return render_to_response(
        template, {
            "contacts_table": ContactTable(Contact.objects.all(), request=req),
            "contact_form": contact_form,
            # no one is using or has tested the bulk form in logistics
            # so we remove it for now
            # "bulk_form": bulk_form,
            "contact": contact,
            "registration_view": reverse(registration_view)
        }, context_instance=RequestContext(req)
    )
