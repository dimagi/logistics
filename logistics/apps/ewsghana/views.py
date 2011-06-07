#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" 
This all is just eye candy to tie these views together one one page
"""

from django.http import HttpResponse
from rapidsms.contrib.messagelog.views import message_log as rapidsms_message_log
from auditcare.views import auditAll
from registration.views import register as django_register
from logistics.apps.logistics.view_decorators import geography_context
from logistics.apps.logistics.views import reporting as logistics_reporting
from logistics.apps.reports.views import email_reports as logistics_email_reports
from logistics.apps.web_registration.forms import AdminRegistersUserForm
from logistics.apps.web_registration.views import admin_does_all

""" Usage-Related Views """
@geography_context
def reporting(request, location_code=None, context={}, template="ewsghana/reporting.html"):
    return logistics_reporting(request=request, location_code=location_code, 
                               context=context, template=template, 
                               destination_url="ewsghana_reporting")
    
def message_log(request, template="ewsghana/messagelog.html"):
    return rapidsms_message_log(request, template)

def auditor(request, template="ewsghana/auditor.html"):
    return auditAll(request, template)

def register_web_user(request, pk=None, Form=AdminRegistersUserForm, 
                   template='web_registration/admin_registration.html', 
                   success_url='admin_web_registration_complete'):
    # non-admin users only get to see the default 'create user' settings
    if not request.user.is_superuser:
        Form = AdminRegistersUserForm
    return admin_does_all(request, pk, Form, template, success_url)

""" Configuration-Related Views """
def web_registration(request, template_name="registration/registration_form.html"):
    return django_register(request)

def email_reports(request, context={}, template="ewsghana/email_reports.html"):
    return logistics_email_reports(request, context, template)

