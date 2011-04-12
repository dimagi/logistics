#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.conf.urls.defaults import *
from django.contrib.auth.views import login as django_login
from django.contrib.auth.views import logout as django_logout

urlpatterns = patterns('',
    # steal the rapidsms login/logouts
url(r'^accounts/login/$', django_login, 
        kwargs={"template_name":"ewsghana/login.html"}, 
        name='rapidsms-login'),
    url(r'^accounts/logout/$', django_logout, 
        kwargs={"template_name":"ewsghana/loggedout.html"},
        name='rapidsms-logout'),
)
