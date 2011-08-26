#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from logistics_project.apps.tanzania.models import SupplyPointStatus

class SupplyPointStatusAdmin(admin.ModelAdmin):
    model = SupplyPointStatus
    list_display = ('status_type', 'status_value', 'supply_point', 'status_date')
    list_filter = ('status_type', 'status_value', 'supply_point', 'status_date')

admin.site.register(SupplyPointStatus, SupplyPointStatusAdmin)