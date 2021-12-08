#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from rapidsms.contrib.messagelog.models import Message
from logistics_project.apps.registration.views import registration as logistics_registration
from logistics_project.apps.web_registration.views import my_web_registration
from logistics import views as logistics_views
from logistics_project.apps.ewsghana.forms import EWSGhanaWebRegistrationForm
from logistics_project.apps.ewsghana.views import register_web_user

urlpatterns = patterns('',
    url(r'^messagelog/export/?$', 'django_tablib.views.export', {
        'model': Message}, name="export_messagelog"),
    url(r'^help/?$', direct_to_template, {'template': 'ewsghana/help.html'}, name="help"),

    url(r'^messagelog/?$', 'logistics_project.apps.ewsghana.views.message_log',
        name="ewsghana_message_log"),
    url(r'^reporting/?$', 'logistics_project.apps.ewsghana.views.reporting', 
        name="ewsghana_reporting"),
    url(r'^(?P<location_code>[\w-]+)/reporting$', 'logistics_project.apps.ewsghana.views.reporting', 
        name="ewsghana_reporting"),
    
    # sms user register
    url(r'^registration/sms/?$', logistics_registration, 
        {'template':'ewsghana/sms_registration.html'}, 
        name="ewsghana_sms_registration"),
    # sms user edit
    url(r'^registration/sms/(?P<pk>\d+)/edit/?$', logistics_registration, 
        {'template':'ewsghana/sms_registration.html'}, 
        name="ewsghana_registration_edit"),
    url(r'^scheduled_reports/?$', 'logistics_project.apps.ewsghana.views.email_reports', 
        name="ewsghana_scheduled_reports"),
    
    # register new user
    url(r'^register/web/admin/?$', register_web_user, 
        {'Form':EWSGhanaWebRegistrationForm, 
         'template':'ewsghana/web_registration.html', 
         'success_url': 'admin_web_registration'},     
       name='admin_web_registration'),
    # modify my account
    url(r'^register/web/me/?$',  my_web_registration,
        {'template':'ewsghana/my_web_registration.html', 
         'success_url': 'my_web_registration'}, 
        name='my_web_registration'),
    # edit existing web user
    url(r'^register/web/(?P<pk>\d+)/edit/?$', register_web_user,
        {'Form':EWSGhanaWebRegistrationForm, 
         'template':'ewsghana/web_registration.html', 
         'success_url': 'admin_web_registration'}, 
        name='admin_web_registration_edit'),
    # web user registration done
    url(r'^register/web/admin/complete(?:/(?P<caller>\w+))?(?:/(?P<account>\w+))?/$',
       direct_to_template,
       { 'template': 'web_registration/admin_registration_complete.html' },
       name='ewsghana_admin_web_registration_complete'),

    url(r'^facility?$',
       logistics_views.facility, 
       { 'template': "ewsghana/config.html"},
       name='facility_view'),
    url(r'^facility/(?P<pk>\d+)/edit/?$',
       logistics_views.facility,
       { 'template':"ewsghana/config.html"},
       name='facility_edit'), 
    url(r'^commodity/?$',
       logistics_views.commodity,                           
       { 'template':"ewsghana/config.html"},
       name='commodity_view'),
    url(r'^commodity/(?P<pk>\d+)/edit/?$',
       logistics_views.commodity, 
       { 'template': "ewsghana/config.html"},
       name='commodity_edit'),
    url(r'^facilities', 
        'logistics_project.apps.ewsghana.views.facilities_list',  
        name="facilities_list"),
    url(r'^(?P<location_code>[\w-]+)/facilities',
        'logistics_project.apps.ewsghana.views.facilities_list',  
        name="facilities_list"),
    url(r'^facility/(?P<code>\w+)/config/?$',
       'logistics_project.apps.ewsghana.views.facility_detail', 
       { 'template':"ewsghana/single_facility.html"},
       name='facility_detail'), 
)
