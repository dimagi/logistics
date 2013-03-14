#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from logistics_project.apps.tanzania.models import SupplyPointStatus,\
    AdHocReport
from rapidsms.contrib.locations.models import Location

class SupplyPointStatusAdmin(admin.ModelAdmin):
    model = SupplyPointStatus
    list_display = ('status_type', 'status_value', 'supply_point', 'status_date')
    list_filter = ('status_type', 'status_value', 'supply_point', 'status_date')

class TzLocationAdmin(admin.ModelAdmin):
    model = Location
    list_display = ("name", "code", "type", "parent", "is_active")
    list_filter = ('type', 'is_active', 'parent_id')

admin.site.register(SupplyPointStatus, SupplyPointStatusAdmin)
admin.site.register(AdHocReport)

try:
    admin.site.unregister(Location)
except Exception:
    pass

admin.site.register(Location, TzLocationAdmin)
