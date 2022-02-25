#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


from django.conf.urls import *

urlpatterns = patterns('',
    url(r'^$',
        "logistics_project.apps.maps.views.dashboard",
        name="maps_dashboard"),
)
