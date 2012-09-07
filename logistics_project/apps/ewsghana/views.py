#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" 
This all is just eye candy to tie these views together one one page
"""

from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from logistics.views import message_log as rapidsms_message_log
from django_tablib import ModelDataset
from django_tablib.base import mimetype_map
from django.views.decorators.cache import cache_page
from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message
from auditcare.views import auditAll
from registration.views import register as django_register
from logistics.models import SupplyPoint
from logistics.view_decorators import geography_context, location_context
from logistics.views import reporting as logistics_reporting
from email_reports.views import email_reports as logistics_email_reports
from logistics_project.apps.web_registration.forms import AdminRegistersUserForm
from logistics_project.apps.web_registration.views import admin_does_all
from logistics_project.apps.ewsghana.tables import FacilityDetailTable
from logistics.util import config

""" Usage-Related Views """
@geography_context
@location_context
def reporting(request, location_code=None, context={}, template="ewsghana/reporting.html"):
    return logistics_reporting(request=request, location_code=location_code, 
                               context=context, template=template, 
                               destination_url="ewsghana_reporting")
    
def message_log(request, template="ewsghana/messagelog.html"):
    return rapidsms_message_log(request, template)

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

def auditor(request, template="ewsghana/auditor.html"):
    return auditAll(request, template)

def register_web_user(request, pk=None, Form=AdminRegistersUserForm, 
                   template='web_registration/admin_registration.html', 
                   success_url='admin_web_registration_complete'):
    # non-admin users only get to see the default 'create user' settings
    if not request.user.is_superuser:
        Form = AdminRegistersUserForm
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
    #facilities = facilities.exclude(type__code=config.SupplyPointCodes.REGIONAL_MEDICAL_STORE)
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
