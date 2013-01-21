#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from logistics_project.apps.ewsghana.models import EscalatingAlertRecipients

class EscalatingAlertRecipientsAdmin(admin.ModelAdmin):
    model = EscalatingAlertRecipients

admin.site.register(EscalatingAlertRecipients, EscalatingAlertRecipientsAdmin)

