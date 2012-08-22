#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from auditcare.views import auditAll
from registration.views import register as django_register
from email_reports.views import email_reports as logistics_email_reports
from logistics.models import Product, SupplyPoint
from logistics.tables import FacilityTable
from logistics.view_decorators import geography_context, location_context
from logistics.views import message_log as rapidsms_message_log
from logistics.views import reporting as logistics_reporting
from logistics_project.apps.web_registration.views import admin_does_all
from logistics_project.apps.ewsghana.tables import FacilityDetailTable
from logistics_project.apps.ewsghana.forms import EWSGhanaSMSRegistrationForm
from logistics_project.apps.ewsghana.permissions import FACILITY_MANAGER_GROUP_NAME
from .forms import FacilityForm, EWSGhanaBasicWebRegistrationForm, \
    EWSGhanaManagerWebRegistrationForm, EWSGhanaAdminWebRegistrationForm
from logistics_project.apps.registration.views import registration as logistics_registration
from .forms import FacilityForm

""" Usage-Related Views """
@geography_context
@location_context
def reporting(request, location_code=None, context={}, template="ewsghana/reporting.html"):
    return logistics_reporting(request=request, location_code=location_code, 
                               context=context, template=template, 
                               destination_url="ewsghana_reporting")
    
def message_log(request, template="ewsghana/messagelog.html"):
    return rapidsms_message_log(request, template)

def auditor(request, template="ewsghana/auditor.html"):
    return auditAll(request, template)

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
    facility = get_object_or_404(SupplyPoint, code=code)
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
    klass = "SupplyPoint"
    if pk is not None:
        facility = get_object_or_404(
            SupplyPoint, pk=pk)
    if req.method == "POST":
        if req.POST["submit"] == "Delete %s" % klass:
            facility.delete()
            return HttpResponseRedirect(
                reverse('facility_view'))
        else:
            form = FacilityForm(instance=facility,
                                data=req.POST)
            if form.is_valid():
                facility = form.save()
                return HttpResponseRedirect(
                    reverse('facility_view'))
    else:
        form = FacilityForm(instance=facility)
    products = Product.objects.filter(is_active=True).order_by('name')
    return render_to_response(
        template, {
            "table": FacilityTable(SupplyPoint.objects.filter(active=True), request=req),
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

