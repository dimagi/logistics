#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from rapidsms.models import Contact
from logistics_project.apps.malawi.models import Organization

class MalawiContactAdmin(admin.ModelAdmin):
    model = Contact
    list_display = ('name', 'supply_point', 'role', 'is_active', 'organization')


admin.site.unregister(Contact)
admin.site.register(Contact, MalawiContactAdmin)
admin.site.register(Organization)

