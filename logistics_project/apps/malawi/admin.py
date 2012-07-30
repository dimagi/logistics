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
    list_display = ('supply_point', 'date', 'total', 'reported', 'on_time')
    list_filter = ('supply_point__type', 'date', 'total', 'reported', 'on_time')

admin.site.register(ProductAvailabilityData)
admin.site.register(ReportingRate, ReportingRateAdmin)
admin.site.register(TimeTracker)
admin.site.register(OrderRequest)
admin.site.register(OrderFulfillment)