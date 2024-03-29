#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from __future__ import unicode_literals
from django.contrib import admin
from .models import App, Backend, Connection, Contact

class ConnectionInline(admin.TabularInline):
    model = Connection
    extra = 1

class ContactAdmin(admin.ModelAdmin):
    model = Contact
    inlines = [
        ConnectionInline,
    ]

class ConnectionAdmin(admin.ModelAdmin):
    model = Connection
    list_display = ["identity", "contact", "backend",]
    list_filter = ["backend", "contact"]
    search_fields = ["identity"]


admin.site.register(App)
admin.site.register(Backend)
admin.site.register(Connection, ConnectionAdmin)
admin.site.register(Contact, ContactAdmin)
