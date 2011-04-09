#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from . import views

urlpatterns = patterns('',
    url(r'^register/web/admin/?$',
       views.admin_does_all,                           
       name='admin_web_registration'),
    url(r'^register/web/admin/complete(?:/(?P<caller>\w+))?(?:/(?P<account>\w+))?/$',
       direct_to_template,
       { 'template': 'web_registration/admin_registration_complete.html' },
       name='admin_web_registration_complete') 
)
