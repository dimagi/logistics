#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *

urlpatterns = patterns('',

    url(r'^$',
        "logistics.apps.malawi.views.dashboard",
        name="malawi_dashboard"),
    url(r'^places/$',
        "logistics.apps.malawi.views.places",
        name="malawi_places"),
    url(r'^contacts/$',
        "logistics.apps.malawi.views.contacts",
        name="malawi_contacts"),
    url(r'^hsas/$',
        "logistics.apps.malawi.views.hsas",
        name="malawi_hsas"),
    url(r'^hsa/(?P<code>\d+)/$',
        "logistics.apps.malawi.views.hsa",
        name="malawi_hsa"),
    url(r'^facilities/$',
        "logistics.apps.malawi.views.facilities",
        name="malawi_facilities"),
    url(r'^facilities/(?P<code>\d+)/$',
        "logistics.apps.malawi.views.facility",
        name="malawi_facility"),
    url(r'^products/$',
        "logistics.apps.malawi.views.products",
        name="malawi_products"),
)
