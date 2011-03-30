#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from logistics.apps.reports.models import *

class WeeklyReportNotificationAdmin(admin.ModelAdmin):
    model = WeeklyReportNotification

class DailyReportNotificationAdmin(admin.ModelAdmin):
    model = DailyReportNotification

admin.site.register(WeeklyReportNotification, WeeklyReportNotificationAdmin)
admin.site.register(DailyReportNotification, DailyReportNotificationAdmin)

