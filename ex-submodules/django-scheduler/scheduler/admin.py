#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from .models import EventSchedule

class EventScheduleAdmin(admin.ModelAdmin):
    model = EventSchedule

admin.site.register(EventSchedule, EventScheduleAdmin)
