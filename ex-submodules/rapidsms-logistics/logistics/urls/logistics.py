#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to, direct_to_template
from ..models import get_geography, ProductStock, ProductReport

urlpatterns = patterns('',
    url(r'^no_ie_allowed/?$', 'logistics.views.no_ie_allowed', 
        name="no_ie_allowed"),
    url(r'^(?P<facility_code>[\w-]+)/input_stock$',
        'logistics.views.input_stock',
        name="input_stock"),
    # ok, so this isn't the most generic, but we don't yet know what the final dashboard will look like
    # so we'll use this as a placeholder until we do
    url(r'^dashboard/?$',
        'logistics.views.dashboard',
        name="logistics_dashboard"),
    url(r'^dashboard/(?P<location_code>[\w-]+)/?$',
        'logistics.views.dashboard',
        name="logistics_dashboard"),
    url(r'^aggregate/?$',
        'logistics.views.aggregate',
        name="aggregate"),
    url(r'^ghana/aggregate/?$',
        'logistics.views.aggregate',
        {'location_code':'ghana'},
        name="aggregate_ghana"),
    url(r'^(?P<location_code>[\w-]+)/aggregate/?$',
        'logistics.views.aggregate',
        name="aggregate"),
    url(r'^(?P<facility_code>[\w-]+)/stockonhand/?$',
        'logistics.views.stockonhand_facility',
        name="stockonhand_facility"),
    url(r'^by_product/(?P<location_code>[\w-]+)/?$',
        'logistics.views.facilities_by_product',
        name="by_product"),
    url(r'^reporting$',
        'logistics.views.reporting',
        name="reporting"),
    url(r'^(?P<location_code>[\w-]+)/reporting$',
        'logistics.views.reporting',
        name="reporting"),
    url(r'^reporting/export/xls$', 'django_tablib.views.export', {
        'queryset': ProductReport.objects.all().order_by('report_date')}, 
        name="export_reporting"),
    url(r'^(?P<facility_code>\w+)/stockonhand/export/xls$', 
        'logistics.views.export_stockonhand',  
        name="export_stock"),
    url(r'^navigate$', 
        'logistics.views.navigate',  
        name="navigate"),
    url(r'^district_dashboard', 
        'logistics.views.district_dashboard',  
        name="district_dashboard"),
)
