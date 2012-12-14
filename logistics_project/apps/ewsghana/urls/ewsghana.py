#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from registration.views import register
from rapidsms.contrib.messagelog.models import Message
from logistics_project.apps.registration.views import registration as logistics_registration
from logistics_project.apps.ewsghana.views import my_web_registration, sms_registration
from logistics import views as logistics_views
from logistics_project.apps.ewsghana.views import register_web_user, configure_incharge, help
from logistics_project.apps.ewsghana.forms import EWSGhanaSelfRegistrationForm
from logistics_project.apps.ewsghana.views import EWSGhanaMessageLogView

urlpatterns = patterns('',
    url(r'^dashboard/?$',
        'logistics_project.apps.ewsghana.views.dashboard',
        name="ghana_dashboard"),
    url(r'^messagelog/export/?$', 'logistics_project.apps.ewsghana.views.export_messagelog', 
        name="export_messagelog"),
    url(r'^help/?$', help, {'template':'ewsghana/help.html'}, name="help"),
    url(r'^auditor/export/?$', 'logistics_project.apps.ewsghana.views.auditor_export', 
        name="auditor_export"),
    url(r'^auditor/?$', 'logistics_project.apps.ewsghana.views.auditor', 
        name="ewsghana_auditor"),
    url(r'^messagelog/?$', EWSGhanaMessageLogView.as_view(), 
        name="ewsghana_message_log"),
    url(r'^reporting/?$', 'logistics_project.apps.ewsghana.views.reporting', 
        name="ewsghana_reporting"),
    url(r'^(?P<location_code>[\w-]+)/reporting$', 'logistics_project.apps.ewsghana.views.reporting', 
        name="ewsghana_reporting"),
    
    # sms user register
    url(r'^registration/sms/?$', sms_registration, 
        {'template':'ewsghana/sms_registration.html'}, 
        name="ewsghana_sms_registration"),
    # sms user edit
    url(r'^registration/sms/(?P<pk>\d+)/edit/?$', sms_registration, 
        {'template':'ewsghana/sms_registration.html'}, 
        name="ewsghana_registration_edit"),
    # configure in charge for a given facility
    url(r'^configure/(?P<sp_code>[\w-]+)/incharge/?$', configure_incharge, 
        name="ews_configure_incharge"),
    url(r'^scheduled_reports/(?P<pk>\d+)/?$', 'logistics_project.apps.ewsghana.views.email_reports', 
        name="ewsghana_scheduled_reports"),
    url(r'^scheduled_reports/?$', 'logistics_project.apps.ewsghana.views.email_reports', 
        name="ewsghana_scheduled_reports"),
    
    # sign up for a new account
    url(r'^accounts/register/$', register, 
        kwargs={"template_name": "registration/registration_form.html", 
                'form_class': EWSGhanaSelfRegistrationForm },
        name='ewsghana_web_register_self'),
    # register new user
    url(r'^register/web/admin/?$', register_web_user, 
        {'template':'ewsghana/web_registration.html', 
         'success_url': 'admin_web_registration'},     
       name='admin_web_registration'),
    # modify my account
    url(r'^me/?$',  my_web_registration,
        {'template':'ewsghana/my_web_registration.html', 
         'success_url': 'my_web_registration'}, 
        name='my_web_registration'),
    # edit existing web user
    url(r'^register/web/(?P<pk>\d+)/edit/?$', register_web_user,
        {'template':'ewsghana/web_registration.html', 
         'success_url': 'admin_web_registration'}, 
        name='admin_web_registration_edit'),
    # web user registration done
    url(r'^register/web/admin/complete(?:/(?P<caller>\w+))?(?:/(?P<account>\w+))?/$',
       direct_to_template,
       { 'template': 'web_registration/admin_registration_complete.html' },
       name='ewsghana_admin_web_registration_complete'),

    url(r'^commodity/?$',
       logistics_views.commodity,                           
       { 'template':"ewsghana/config.html"},
       name='commodity_view'),
    url(r'^commodity/(?P<pk>\d+)/edit/?$',
       logistics_views.commodity, 
       { 'template': "ewsghana/config.html"},
       name='commodity_edit'),
    url(r'^commodity/(?P<sms_code>\w+)/activate/?$',
       logistics_views.activate_commodity,
       name='commodity_activate'),
    url(r'^facility?$',
        'logistics_project.apps.ewsghana.views.facility',
       name='facility_view'),
    url(r'^facility/(?P<pk>\d+)/edit/?$',
       'logistics_project.apps.ewsghana.views.facility',
       name='facility_edit'), 
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
    url(r'^medical_stores/?$',
        'logistics_project.apps.ewsghana.views.medical_stores',
        name="medical_stores"),
)
