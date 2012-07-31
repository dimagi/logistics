#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from rapidsms.models import Contact
from logistics_project.apps.malawi.models import Organization
from logistics_project.apps.malawi.warehouse_models import *

class MalawiContactAdmin(admin.ModelAdmin):
    model = Contact
    list_display = ('name', 'supply_point', 'role', 'is_active', 'organization')


admin.site.unregister(Contact)
admin.site.register(Contact, MalawiContactAdmin)
admin.site.register(Organization)

# warehouse admin
class ReportingRateAdmin(admin.ModelAdmin):
    model = ReportingRate
    list_display = ('supply_point', 'date', 'total', 'reported', 'on_time', 'complete')
    list_filter = ('supply_point__type', 'date', 'supply_point')

class ProductAvailabilityDataAdmin(admin.ModelAdmin):
    model = ProductAvailabilityData
    list_display = ('supply_point', 'product', 'date', 'total', 'managed', 
                    'with_stock', 'under_stock', 'over_stock', 'without_stock', 
                    'without_data')
    list_filter = ('supply_point__type', 'product', 'date', 'supply_point')

admin.site.register(ProductAvailabilityData, ProductAvailabilityDataAdmin)
admin.site.register(ReportingRate, ReportingRateAdmin)
admin.site.register(TimeTracker)
admin.site.register(OrderRequest)
admin.site.register(OrderFulfillment)