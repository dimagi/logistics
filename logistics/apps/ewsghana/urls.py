#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from rapidsms.contrib.messagelog.models import Message
from logistics.apps.registration.views import registration as logistics_registration

urlpatterns = patterns('',
    url(r'^messagelog/export/?$', 'django_tablib.views.export', {
        'model': Message}, name="export_messagelog"),
    url(r'^help/?$', direct_to_template, {'template': 'ewsghana/help.html'}, name="help"),

    url(r'^auditor/?$', 'logistics.apps.ewsghana.views.auditor', 
        name="ewsghana_auditor"),
    url(r'^messagelog/?$', 'logistics.apps.ewsghana.views.message_log', 
        name="ewsghana_message_log"),
    url(r'^reporting/?$', 'logistics.apps.ewsghana.views.reporting', 
        name="ewsghana_reporting"),
        
    url(r'^registration/sms/?$', logistics_registration, 
        {'template':'ewsghana/sms_registration.html'}, 
        name="ewsghana_sms_registration"),
    url(r'^registration/sms/(?P<pk>\d+)/edit/?$', logistics_registration, 
        {'template':'ewsghana/sms_registration.html'}, 
        name="ewsghana_registration_edit"),
    url(r'^registration/web/?$', 'logistics.apps.ewsghana.views.web_registration', 
        name="ewsghana_web_registration"),
    url(r'^scheduled_reports/?$', 'logistics.apps.ewsghana.views.email_reports', 
        name="ewsghana_scheduled_reports")
)
