#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import re
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db import transaction
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from rapidsms.contrib.messaging.utils import send_message
from rapidsms.models import Connection
from rapidsms.models import Backend
from rapidsms.models import Contact
from logistics.models import SupplyPoint
from logistics_project.apps.registration.forms import CommoditiesContactForm, \
    BulkRegistrationForm
from logistics_project.apps.registration.validation import check_for_dupes, \
    intl_clean_phone_number
from .tables import ContactTable

@permission_required('rapidsms.add_contact')
def registration(req, pk=None, template="registration/dashboard.html", 
                 contact_form=CommoditiesContactForm):
    context = {}
    contact = None
    connection = None
    search = None
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
            connection = contact.default_connection
        except Connection.DoesNotExist:
            connection = None
    if req.method == "POST":
        if req.POST["submit"] == "Delete Number":
            conn = Connection.objects.get(pk=req.POST['number_to_delete'])
            conn.delete()
            return HttpResponseRedirect("%s" % (reverse(registration_edit, 
                                                        kwargs={'pk':contact.pk})))
        elif req.POST["submit"] == "Add Number":
            phone_number = req.POST['phone_to_add']
            try:
                check_for_dupes(phone_number)
                intl_clean_phone_number(phone_number)
            except ValidationError, e:
                context['errors'] = e.messages[0] if e.messages else None
                contact_form = contact_form(
                    instance=contact)
            else:
                contact.add_phone_number(phone_number)
                return HttpResponseRedirect("%s" % (reverse(registration_edit, 
                                                            kwargs={'pk':contact.pk})))
        elif req.POST["submit"] == "Delete Contact":
            # deactivate instead of delete to preserve logs
            name = unicode(contact)
            contact.deactivate()
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

                bcontact = Contact(name=name)
                bcontact.save()
                # TODO deal with errors!
                backend = Backend.objects.get(name=backend_name)

                connection = Connection(backend=backend, identity=identity,\
                    contact=bcontact)
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
    created = None
    deleted = None
    contacts = Contact.objects.filter(is_active=True)
    if req.method == "GET":
        if "created" in req.GET:
            created = req.GET['created']
        elif "deleted" in req.GET:
            deleted = req.GET['deleted']
        if 'search' in req.GET:
            search = req.GET['search']
            # this is here because otherwise searching for "+233"
            # makes postgres complain that '+' is not preceded by a #
            safe_search = re.escape(search)
            contacts = contacts.filter(Q(name__iregex=safe_search) |\
                                       Q(connection__identity__iregex=safe_search) |\
                                       Q(supply_point__name__iregex=safe_search))
    context["other_phones"] = contact.get_other_connections() if contact else None
    context["contacts_table"] = ContactTable(contacts, request=req)
    context["contact_form"] = contact_form
    context["created"] = created
    context["deleted"] = deleted 
    context["search"] = search
    context["contact"] = contact
    context["registration_view"] = reverse(registration_view)
    return render_to_response(
        template, context, context_instance=RequestContext(req)
    )
