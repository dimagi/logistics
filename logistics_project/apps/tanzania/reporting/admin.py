#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from logistics_project.apps.tanzania.reporting.models import *

class OrganizationSummaryAdmin(admin.ModelAdmin):
    model = OrganizationSummary
    list_display = ('organization', 'date', 'total_orgs', 'average_lead_time_in_days')
    list_filter = ('organization', 'date')

class GroupSummaryAdmin(admin.ModelAdmin):
    model = GroupSummary
    list_display = ('org_summary', 'title', 'historical_responses', 'no_responses')
    list_filter = ('org_summary', 'title')
    
    
class GroupDataAdmin(admin.ModelAdmin):
    model = GroupData
    list_display = ('group_summary', 'label', 'number')
    list_filter = ('group_summary', 'label')

class ProductAvailabilityDataAdmin(admin.ModelAdmin):
    model = ProductAvailabilityData
    list_display = ('organization', 'date', 'product', 'total', 'with_stock', 
                    'without_stock', 'without_data')
    list_filter = ('organization', 'date', 'product')
    
admin.site.register(OrganizationSummary, OrganizationSummaryAdmin)
admin.site.register(GroupSummary, GroupSummaryAdmin)
admin.site.register(GroupData, GroupDataAdmin)
admin.site.register(ProductAvailabilityData, ProductAvailabilityDataAdmin)