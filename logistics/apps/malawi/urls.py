#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *

urlpatterns = patterns('',

    url(r'^$',
        "logistics.apps.malawi.views.dashboard",
        name="malawi_dashboard"),
    url(r'^contacts/$',
        "logistics.apps.malawi.views.contacts",
        name="malawi_contacts"),
)
