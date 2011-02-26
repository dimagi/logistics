#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
from logistics.apps.logistics.models import get_geography

urlpatterns = patterns('',
    url(r'^input_stock$', 'logistics.apps.logistics.views.input_stock', name="input_stock"),
    url(r'^(?P<location_code>\w+)/aggregate/?$', 'logistics.apps.logistics.views.aggregate', name="aggregate"),
    url(r'^ghana/aggregate/?$', 'logistics.apps.logistics.views.aggregate', kwargs={'location_code':get_geography().code}, name="aggregate_top"),
    url(r'^(?P<facility_code>\w+)/stockonhand/?$', 'logistics.apps.logistics.views.stockonhand', name="stockonhand"),
    url(r'^reporting$', 'logistics.apps.logistics.views.reporting', name="reporting"),
)
