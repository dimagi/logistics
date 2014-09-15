#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from logistics.models import SupplyPoint
from logistics_project.apps.tanzania.models import SupplyPointStatus,\
    AdHocReport
from rapidsms.contrib.locations.models import Location
from rapidsms.contrib.messagelog.models import Message


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

class MessageAdmin(admin.ModelAdmin):
    list_display = ('text', 'direction', 'who', 'date')
    list_filter = ('direction', 'contact', 'connection', 'date')

try:
    admin.site.unregister(Message)
except Exception:
    pass

admin.site.register(Message, MessageAdmin)

try:
    admin.site.unregister(SupplyPoint)
except Exception:
    pass

class SupplyPointAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "type")
    list_filter = ('type', 'active', 'is_pilot')
    model = SupplyPoint

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = []
        if not obj.is_pilot:
            self.exclude = ['nearests_supply_points']
        return super(SupplyPointAdmin, self).get_form(request, obj, **kwargs)

admin.site.register(SupplyPoint, SupplyPointAdmin)
