#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls import *
from . import views


urlpatterns = patterns('',

    url(r'^$',
        views.registration,
        name="registration"),

    url(r'^search$',
        views.search,
        name="search"),

    url(r'^(?P<pk>\d+)/edit$',
        views.registration,
        name="registration_edit")
)
