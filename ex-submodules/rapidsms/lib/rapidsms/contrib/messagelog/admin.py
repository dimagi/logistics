#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from __future__ import unicode_literals
from django.contrib import admin
from .models import Message


class MessageAdmin(admin.ModelAdmin):
    list_display = ("text", "direction", "who", "date", "connection")
    list_filter = ("direction", "date", "connection__backend")

admin.site.register(Message, MessageAdmin)
