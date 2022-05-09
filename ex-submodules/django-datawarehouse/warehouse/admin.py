from __future__ import unicode_literals
from django.contrib import admin
from warehouse.models import ReportRun

class ReportRunAdmin(admin.ModelAdmin):
    model = ReportRun
    list_display = ('start_run', 'end_run', 'start', 'end', 'complete', 'has_error')

admin.site.register(ReportRun, ReportRunAdmin)

