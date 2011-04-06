#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" 
This all is just eye candy to tie these views together one one page
"""

from django.http import HttpResponse
from logistics.apps.logistics.view_decorators import geography_context
from logistics.apps.logistics.views import reporting as logistics_reporting
from rapidsms.contrib.messagelog.views import message_log as rapidsms_message_log
from auditcare.views import auditAll
from rapidsms.contrib.registration.views import registration as rapidsms_registration
from logistics.apps.reports.views import email_reports as logistics_email_reports

@geography_context
def reporting(request, location_code=None, context={}, template="ewsghana/reporting.html"):
    return logistics_reporting(request=request, location_code=location_code, 
                               context=context, template=template)
    
def message_log(request, template="ewsghana/messagelog.html"):
    return rapidsms_message_log(request, template)

def auditor(request, template="ewsghana/auditor.html"):
    return auditAll(request, template)


def sms_registration(request, pk=None, template="ewsghana/sms_registration.html"):
    return rapidsms_registration(request, pk, template)

def web_registration(request, template="ewsghana/web_registration.html"):
    return HttpResponse('ok')

def email_reports(request, context={}, template="ewsghana/email_reports.html"):
    return logistics_email_reports(request, context, template)
