#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
from logistics.apps.logistics.models import get_geography

urlpatterns = patterns('',
    url(r'^(?P<facility_code>\w+)/input_stock$', 'logistics.apps.logistics.views.input_stock', name="input_stock"),
    # ok, so this isn't the most generic, but we don't yet know what the final dashboard will look like
    # so we'll use this as a placeholder until we do
    url(r'^ghana/aggregate/?$', 'logistics.apps.logistics.views.aggregate', {'location_code':'ghana'}, name="aggregate_ghana"),
    url(r'^(?P<location_code>\w+)/aggregate/?$', 'logistics.apps.logistics.views.aggregate', name="aggregate"),
    url(r'^(?P<facility_code>\w+)/stockonhand/?$', 'logistics.apps.logistics.views.stockonhand', name="stockonhand"),
    url(r'^reporting$', 'logistics.apps.logistics.views.reporting', name="reporting"),
)
