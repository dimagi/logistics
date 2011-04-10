#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # steal the rapidsms login/logouts
    url(r'^accounts/login/$', 'auth_login', name='rapidsms-login'),
    url(r'^accounts/logout/$', 'auth_logout', name='rapidsms-logout'),
)
