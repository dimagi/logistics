#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from __future__ import unicode_literals
from django.conf.urls import *
from .. import views

urlpatterns = patterns('',
    url(r'^login/$', views.login, name='rapidsms-login'),
    url(r'^logout/$', views.logout, name='rapidsms-logout'),
)
