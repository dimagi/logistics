#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'account/(?P<user_id>[\w-]+)/new_report_schedule/$', 
        'logistics.apps.reports.views.add_scheduled_report', 
        name='add_scheduled_report'),
    url(r'account/(?P<user_id>[\w-]+)/drop_scheduled_report/(?P<report_id>[\w-]+)/?$', 
        'logistics.apps.reports.views.drop_scheduled_report', 
        name='drop_scheduled_report'),
    url(r'account/(?P<user_id>[\w-]+)/test_report_schedule/(?P<report_id>[\w-]+)/?$', 
        'logistics.apps.reports.views.test_scheduled_report', 
        name='test_scheduled_report'),
    url(r'/?$', 
        'logistics.apps.reports.views.email_reports', 
        name='email_reports'),
)
