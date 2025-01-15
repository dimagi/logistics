#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from __future__ import unicode_literals
from django.contrib import admin
from rapidsms.models import Contact
from logistics_project.apps.malawi.models import Organization
from logistics_project.apps.malawi.warehouse.models import *

class MalawiContactAdmin(admin.ModelAdmin):
    model = Contact
    list_display = ('name', 'supply_point', 'role', 'is_active', 'organization')


admin.site.unregister(Contact)
admin.site.register(Contact, MalawiContactAdmin)
admin.site.register(Organization)

# warehouse admin
class ReportingRateAdmin(admin.ModelAdmin):
    model = ReportingRate
    list_display = ('supply_point', 'date', 'base_level', 'total', 'reported', 'on_time', 'complete')
    list_filter = ('supply_point__type', 'date', 'base_level', 'supply_point')
    search_fields = ['supply_point__name']


class ProductAvailabilityDataAdmin(admin.ModelAdmin):
    model = ProductAvailabilityData
    list_display = ('supply_point', 'product', 'date', 'total', 'managed',
                    'with_stock', 'under_stock', 'over_stock', 'without_stock',
                    'without_data')
    list_filter = ('supply_point__type', 'product', 'date', 'supply_point')

class ProductAvailabilityDataSummaryAdmin(admin.ModelAdmin):
    model = ProductAvailabilityDataSummary
    list_display = ('supply_point', 'date', 'base_level', 'total', 'any_managed', 'any_without_stock')
    list_filter = ('supply_point__type', 'date', 'base_level', 'supply_point')

class TimeTrackerAdmin(admin.ModelAdmin):
    model = TimeTracker
    list_display = ('supply_point', 'date', 'type', 'total', 'time_in_seconds')
    list_filter = ('supply_point__type', 'date', 'type')

class OrderRequestAdmin(admin.ModelAdmin):
    model = OrderRequest
    list_display = ('supply_point', 'date', 'product', 'total', 'emergency')
    list_filter = ('supply_point__type', 'date', 'product')

class CalculatedConsumptionAdmin(admin.ModelAdmin):
    model = CalculatedConsumption
    # list_display = ('supply_point', 'date', 'product', 'calculated_consumption',
    #                 'time_stocked_out', 'time_with_data', 'time_needing_data')
    list_filter = ('supply_point__type', 'date', 'product')
    search_fields = ['supply_point__name']

class CurrentConsumptionAdmin(admin.ModelAdmin):
    model = CurrentConsumption
    list_display = ('supply_point', 'product', 'total',
                    'current_daily_consumption', 'stock_on_hand')
    list_filter = ('supply_point__type', 'product')


admin.site.register(ProductAvailabilityData, ProductAvailabilityDataAdmin)
admin.site.register(ProductAvailabilityDataSummary, ProductAvailabilityDataSummaryAdmin)
admin.site.register(ReportingRate, ReportingRateAdmin)
admin.site.register(TimeTracker, TimeTrackerAdmin)
admin.site.register(OrderRequest, OrderRequestAdmin)
admin.site.register(OrderFulfillment)
admin.site.register(CalculatedConsumption, CalculatedConsumptionAdmin)
admin.site.register(CurrentConsumption, CurrentConsumptionAdmin)
