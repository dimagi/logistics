from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',
    url(r'^dashboard/$', 'logistics_project.apps.tanzania.views.dashboard', name="tz_dashboard"),
    url('^facilities/index/$', 'logistics_project.apps.tanzania.views.facilities_index', name="facilities_index"),
    url(r'^facilities/(?P<facility_id>\d+)/message_history/$', 'logistics_project.apps.tanzania.views.facility_messages', name="facility_messages"),
#    (r'^facilities/(?P<facility_id>\d+)/note_history/$', 'ilsgateway.views.note_history'),
    url('^facility/(?P<facility_id>\d+)/$', 'logistics_project.apps.tanzania.views.facility_details', name="tz_facility_details"),
#    url('^facilities/ordering/$', 'logistics_project.apps.tanzania.views.facilities_ordering', name="ordering"),
#    (r'^doclist', 'ilsgateway.views.doclist'),
#    url(r'^supervision/$', 'logistics_project.apps.tanzania.views.supervision', name='supervision'),
#    url(r'^reports/$', 'logistics_project.apps.tanzania.views.new_reports', name='reports'),
    url(r'^reports/(?P<slug>\w+)/$', 'logistics_project.apps.tanzania.reportcalcs.new_reports', name='new_reports'),
    url(r'^reports/$', 'logistics_project.apps.tanzania.reportcalcs.new_reports', name='new_reports'),
#    url(r'^reports/pdf/$', 'logistics_project.apps.tanzania.views.reporting_pdf', name="tz_pdf_reports"),
#    url(r'^reports/adhoc/$', 'logistics_project.apps.tanzania.views.ad_hoc_reports',
#        name='ad_hoc_reports'),
    
#    (r'^stockinquiry', 'ilsgateway.views.stock_inquiry'),
    url(r'^docdownload/(?P<facility_id>\w+)/$', 'logistics_project.apps.tanzania.views.docdownload', name="tz_docdownload"),
    url(r'^change_language/$', 'logistics_project.apps.tanzania.views.change_language', name="tz_language"),
    url(r'^change_language/post/$', 'logistics_project.apps.tanzania.views.change_language_real', name="tz_language_redirect"),
    url(r'^schedule/$', direct_to_template, {'template': 'tanzania/sms_schedule.html'}, name="tz_sms_schedule"),
)
