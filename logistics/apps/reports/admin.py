#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from logistics.apps.reports.models import *

class WeeklyReportSubscriptionAdmin(admin.ModelAdmin):
    model = WeeklyReportSubscription

class DailyReportSubscriptionAdmin(admin.ModelAdmin):
    model = DailyReportSubscription

admin.site.register(WeeklyReportSubscription, WeeklyReportSubscriptionAdmin)
admin.site.register(DailyReportSubscription, DailyReportSubscriptionAdmin)

