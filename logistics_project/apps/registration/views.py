#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.conf import settings
from django.db.models import Q
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
from logistics.models import SupplyPoint
from logistics_project.apps.registration.forms import CommoditiesContactForm, BulkRegistrationForm
from .tables import ContactTable

@permission_required('rapidsms.add_contact')
def registration(req, pk=None, template="registration/dashboard.html", 
                 contact_form=CommoditiesContactForm):
    contact = connection = bulk_form = search = None
    registration_view = 'registration'
    registration_edit = 'registration_edit'
    if hasattr(settings, 'SMS_REGISTRATION_VIEW'):
        registration_view = settings.SMS_REGISTRATION_VIEW
    if hasattr(settings, 'SMS_REGISTRATION_EDIT'):
        registration_edit = settings.SMS_REGISTRATION_EDIT

    if pk is not None:
        contact = get_object_or_404(
            Contact, pk=pk)
        try:
            connection = Connection.objects.get(contact=contact)
        except Connection.DoesNotExist:
            connection = None
    if req.method == "POST":
        if req.POST["submit"] == "Delete Contact":
            name = unicode(contact)
            contact.delete()
            return HttpResponseRedirect("%s?deleted=%s" % (reverse(registration_view), name))
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
            contact_form = contact_form(
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
                    return HttpResponseRedirect("%s?created=%s" % (reverse(registration_edit, 
                                                                           kwargs={'pk':contact.pk}),
                                                                           unicode(contact)))
    else:
        if pk is None:
            supplypoint = None
            if "supplypoint" in req.GET and req.GET["supplypoint"]:
                try:
                    supplypoint = SupplyPoint.objects.get(code=req.GET["supplypoint"])
                except SupplyPoint.DoesNotExist, SupplyPoint.MultipleObjectsReturned:
                    pass
            contact_form = contact_form(
                instance=contact, 
                initial={'supply_point':supplypoint})
        else:
            contact_form = contact_form(
                instance=contact)
        bulk_form = BulkRegistrationForm()
    created = deleted = None
    contacts = Contact.objects.all()
    if req.method == "GET":
        if "created" in req.GET:
            created = req.GET['created']
        elif "deleted" in req.GET:
            deleted = req.GET['deleted']
        if 'search' in req.GET:
            search = req.GET['search']
            contacts = contacts.filter(Q(name__iregex=search) |\
                                       Q(connection__identity__iregex=search) |\
                                       Q(supply_point__name__iregex=search))
    return render_to_response(
        template, {
            "contacts_table": ContactTable(contacts, request=req),
            "contact_form": contact_form,
            "created": created, 
            "deleted": deleted, 
            "search": search, 
            # no one is using or has tested the bulk form in logistics
            # so we remove it for now
            # "bulk_form": bulk_form,
            "contact": contact,
            "registration_view": reverse(registration_view)
        }, context_instance=RequestContext(req)
    )
