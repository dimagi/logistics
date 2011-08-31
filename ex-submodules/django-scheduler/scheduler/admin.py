#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from .models import EventSchedule
from scheduler.models import ExecutionRecord

class EventScheduleAdmin(admin.ModelAdmin):
    model = EventSchedule

class ExecutionRecordAdmin(admin.ModelAdmin):
    list_display = ["schedule", "runtime" ]
    list_filter = ["schedule"]
    model = ExecutionRecord

admin.site.register(EventSchedule, EventScheduleAdmin)
admin.site.register(ExecutionRecord, ExecutionRecordAdmin)
