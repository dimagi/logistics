#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from rapidsms.contrib.messagelog.models import Message
from logistics.apps.registration.views import registration as logistics_registration
from logistics.apps.web_registration.views import admin_does_all

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
    
    # sms user register
    url(r'^registration/sms/?$', logistics_registration, 
        {'template':'ewsghana/sms_registration.html'}, 
        name="ewsghana_sms_registration"),
    # sms user edit
    url(r'^registration/sms/(?P<pk>\d+)/edit/?$', logistics_registration, 
        {'template':'ewsghana/sms_registration.html'}, 
        name="ewsghana_registration_edit"),
    url(r'^scheduled_reports/?$', 'logistics.apps.ewsghana.views.email_reports', 
        name="ewsghana_scheduled_reports"),
    
    # register new user
    url(r'^register/web/admin/?$', admin_does_all,   
        {'template':'ewsghana/web_registration.html', 
         'success_url': 'ewsghana_admin_web_registration_complete'},     
       name='admin_web_registration'),
    # edit existing web user
    url(r'^register/web/(?P<pk>\d+)/edit/?$', admin_does_all,
        {'template':'ewsghana/web_registration.html', 
         'success_url': 'ewsghana_admin_web_registration_complete'}, 
        name='admin_web_registration_edit'),
    # web user registration done
    url(r'^register/web/admin/complete(?:/(?P<caller>\w+))?(?:/(?P<account>\w+))?/$',
       direct_to_template,
       { 'template': 'web_registration/admin_registration_complete.html' },
       name='admin_web_registration_complete'),
)
