#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from warehouse.models import ReportRun

class ReportRunAdmin(admin.ModelAdmin):
    model = ReportRun
    list_display = ('start_run', 'end_run', 'start', 'end', 'complete', 'has_error')

admin.site.register(ReportRun, ReportRunAdmin)

