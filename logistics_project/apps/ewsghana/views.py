#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from itertools import chain
from django.contrib.auth.models import User
from django.contrib.auth.decorators import permission_required, login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django_tablib import ModelDataset
from django_tablib.base import mimetype_map
from django.views.decorators.cache import cache_page
from dimagi.utils import csv 
from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message
from auditcare.views import auditAll
from auditcare.models import AccessAudit
from registration.views import register as django_register
from email_reports.views import email_reports as logistics_email_reports
from logistics.models import Product, SupplyPoint, LogisticsProfile
from logistics.tables import FacilityTable
from logistics.view_decorators import geography_context, location_context
from logistics.views import message_log as logistics_messagelog
from logistics.views import reporting as logistics_reporting
from logistics.util import config
from logistics_project.apps.web_registration.views import admin_does_all
from logistics_project.apps.ewsghana.tables import FacilityDetailTable
from logistics_project.apps.ewsghana.models import GhanaFacility
from logistics_project.apps.ewsghana.forms import EWSGhanaSMSRegistrationForm
from logistics_project.apps.ewsghana.permissions import FACILITY_MANAGER_GROUP_NAME
from .forms import FacilityForm, EWSGhanaBasicWebRegistrationForm, \
    EWSGhanaManagerWebRegistrationForm, EWSGhanaAdminWebRegistrationForm
from logistics_project.apps.registration.views import registration as logistics_registration
from .forms import FacilityForm
from .tables import AuditLogTable

""" Usage-Related Views """
@geography_context
@location_context
def reporting(request, location_code=None, context={}, template="ewsghana/reporting.html"):
    return logistics_reporting(request=request, location_code=location_code, 
                               context=context, template=template, 
                               destination_url="ewsghana_reporting")
    
def message_log(request, template="ewsghana/messagelog.html"):
    return logistics_messagelog(request, template=template)

@cache_page(60 * 15)
def export_messagelog(request, format='xls'):
    class MessageDataSet(ModelDataset):
        class Meta:
            # hack to limit the # of messages returns
            # so that we don't crash the server when the log gets too big
            # in the long term, should implement asynchronous processing + progress bar
            queryset = Message.objects.order_by('-date')[:10000]
    dataset = getattr(MessageDataSet(), format)
    response = HttpResponse(
        dataset,
        mimetype=mimetype_map.get(format, 'application/octet-stream')
        )
    response['Content-Disposition'] = 'attachment; filename=messagelog.xls'
    return response

def help(request, template="ewsghana/help.html"):
    commodities = Product.objects.filter(is_active=True).order_by('name')
    return render_to_response(
        template, {'commodities':commodities}, 
        context_instance=RequestContext(request)
    )
    
def _prep_audit_for_display(auditevents):
    realEvents = []
    for a in auditevents:
        designation = organization = facility = location = first_name = last_name = ''
        try:
            user = User.objects.get(username=a.user)
        except User.DoesNotExist:
            # OK - anonymous user
            pass
        else:
            first_name = user.first_name
            last_name = user.last_name
            try:
                profile = user.get_profile()
            except LogisticsProfile.DoesNotExist:
                profile = None
            else:
                designation = profile.designation if profile.designation else '' 
                organization = profile.organization if profile.organization else ''
                facility = profile.supply_point if profile.supply_point else ''
                location = profile.location if profile.location else ''
        realEvents.append({'user': a.user, 
                           'date': a.event_date, 
                           'class': a.doc_type, 
                           'access_type': a.access_type, 
                           'first_name': first_name,
                           'last_name': last_name,
                           'designation': designation, 
                           'organization': organization, 
                           'facility': facility, 
                           'location': location })
    return realEvents

def auditor_export(request):
    auditEvents = AccessAudit.view("auditcare/by_date_access_events", 
                                   descending=True, include_docs=True).all()
    detailedEvents = _prep_audit_for_display(auditEvents)
    response = HttpResponse(mimetype=mimetype_map.get(format, 'application/octet-stream'))
    response['Content-Disposition'] = 'attachment; filename=webusage.xls'
    writer = csv.UnicodeWriter(response)
    writer.writerow(["Date ", "User", "Access_Type", "Designation", 
                     "Organization", "Facility", "Location", "First_Name", 
                     "Last_Name"])
    for e in detailedEvents:
        writer.writerow([e['date'], e['user'], e['class'], e['designation'],
                         e['organization'], e['facility'], e['location'], 
                         e['first_name'], e['last_name']])
    return response    

def auditor(request, template="ewsghana/auditor.html"):
    """
    NOTE: this truncates the log by default to the last 750 entries
    To get the complete usage log, web users should export to excel 
    This does a wildly inefficient couch<->postgres join. optimize later if need be.
    """
    MAX_ENTRIES = 500
    if request.method == "GET" and 'search' in request.GET:
            search = request.GET['search']
            auditEvents = AccessAudit.view("auditcare/by_user_access_events", 
                                   limit=MAX_ENTRIES, endkey=[search], 
                                   startkey=[search, {}, {}, {}, {}, {}, {}], 
                                   descending=True, include_docs=True).all()
    else:
            auditEvents = AccessAudit.view("auditcare/by_date_access_events", 
                                   limit=MAX_ENTRIES, 
                                   descending=True, include_docs=True).all()
    detailedEvents = _prep_audit_for_display(auditEvents)
    return render_to_response(template, 
                              {"audit_table": AuditLogTable(detailedEvents, request=request)}, 
                              context_instance=RequestContext(request))

def register_web_user(request, pk=None, 
                   template='web_registration/admin_registration.html', 
                   success_url='admin_web_registration_complete'):
    if request.user.is_superuser:
        Form = EWSGhanaAdminWebRegistrationForm
    elif request.user.groups.filter(name=FACILITY_MANAGER_GROUP_NAME).exists():
        Form = EWSGhanaManagerWebRegistrationForm
    else:
        Form = EWSGhanaBasicWebRegistrationForm
    return admin_does_all(request, pk, Form, 
                          template=template, 
                          success_url=success_url)

""" Configuration-Related Views """
def web_registration(request, template_name="registration/registration_form.html"):
    return django_register(request)

def email_reports(request, context={}, template="ewsghana/email_reports.html"):
    return logistics_email_reports(request, context, template)

@location_context
def facilities_list(request, location_code=None, context={}, template="ewsghana/facilities_list.html"):
    facilities = context['location'].all_facilities()
    context ['table'] = FacilityDetailTable(facilities, request=request)
    context['destination_url'] = "facilities_list"
    return render_to_response(
        template, context, context_instance=RequestContext(request)
    )

def facility_detail(request, code, context={}, template="ewsghana/single_facility.html"):
    facility = get_object_or_404(GhanaFacility, code=code)
    context ['facility'] = facility
    return render_to_response(
        template, context, context_instance=RequestContext(request)
    )

""" Customized Views """

@permission_required('logistics.add_supplypoint')
@transaction.commit_on_success
def facility(req, pk=None, template="ewsghana/facilityconfig.html"):
    facility = None
    form = None
    incharges = None
    klass = "Facility"
    if pk is not None:
        facility = get_object_or_404(
            GhanaFacility, pk=pk)
        incharges = list(chain(facility.reportees(), facility.supervised_by.reportees() if facility.supervised_by else []))
    if req.method == "POST":
        if req.POST["submit"] == "Delete %s" % klass:
            facility.deactivate()
            return HttpResponseRedirect(
                "%s?deleted=%s" % (reverse('facility_view'), 
                                   unicode(facility)))
        else:
            form = FacilityForm(instance=facility,
                                data=req.POST)
            if form.is_valid():
                facility = form.save()
                if pk is not None:
                    url = "%s?updated=%s"
                else:
                    url = "%s?created=%s"
                return HttpResponseRedirect(
                    url % (reverse('facility_edit', kwargs={'pk':facility.pk}), 
                                       unicode(facility)))
    else:
        form = FacilityForm(instance=facility)
    products = Product.objects.filter(is_active=True).order_by('name')
    created = None
    deleted = None
    if req.method == "GET":
        if "created" in req.GET:
            created = req.GET['created']
        elif "deleted" in req.GET:
            deleted = req.GET['deleted']
    return render_to_response(
        template, {
            "created": created, 
            "deleted": deleted, 
            "incharges": incharges,
            "table": FacilityTable(GhanaFacility.objects.filter(active=True), request=req),
            "form": form,
            "object": facility,
            "klass": klass,
            "klass_view": reverse('facility_view'), 
            "products": products
        }, context_instance=RequestContext(req)
    )
    
@transaction.commit_on_success
def my_web_registration(request, 
                        template='web_registration/admin_registration.html', 
                        success_url='admin_web_registration_complete'):
    context = {}
    context['hide_delete'] = True
    Form = EWSGhanaBasicWebRegistrationForm
    return admin_does_all(request, request.user.pk, Form, context, template, success_url)

def sms_registration(request, *args, **kwargs):
    kwargs['contact_form'] = EWSGhanaSMSRegistrationForm
    ret = logistics_registration(request, *args, **kwargs)
    return ret

def configure_incharge(request, sp_code, template="ewsghana/config_incharge.html"):
    klass = "Facility"
    facility = get_object_or_404(GhanaFacility, code=sp_code)
    if request.method == "POST":
        if request.POST["submit"] == "Save In-Charge":
            if "incharge_pk" in request.POST and request.POST["incharge_pk"]:
                incharge = Contact.objects.get(pk=int(request.POST["incharge_pk"]))
                if incharge in facility.reportees():
                    # if it's a supervisor @ this facility, then no need to add supervised_by
                    # just remove it
                    if facility.supervised_by is not None:
                        facility.supervised_by = None
                        facility.save()
                elif incharge.supply_point != facility.supervised_by:
                    facility.supervised_by = incharge.supply_point
                    facility.save()
        return HttpResponseRedirect(
            reverse('facility_edit', kwargs={"pk":facility.pk}))
    form = FacilityForm(instance=facility)
    for key in form.fields.keys():
        form.fields[key].widget.attrs['disabled'] = True
        form.fields[key].widget.attrs['readonly'] = True
    return render_to_response(
        template, {
            "candidates": facility.get_district_incharges(), 
            "form": form,
            "object": facility,
            "klass": klass,
            "klass_view": reverse('facility_view')
        }, context_instance=RequestContext(request)
    )
