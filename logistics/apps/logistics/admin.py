#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from logistics.apps.logistics.models import *

class ConnectionInline(admin.TabularInline):
    model = Connection
    extra = 1

class ContactDetailAdmin(admin.ModelAdmin):
    model = ContactDetail
    list_display = ('name', 'role', 'service_delivery_point')
    inlines = [
        ConnectionInline,
    ]

class ContactRoleAdmin(admin.ModelAdmin):
    model = ContactRole

class ProductAdmin(admin.ModelAdmin):
    model = Product
    list_display = ('name', 'units', 'sms_code', 'description','product_code')

class RegionAdmin(admin.ModelAdmin):
    model = Region

class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_delivery_point_type')
    ordering = ['name']

class FacilityAdmin(admin.ModelAdmin):
    model = Facility
    list_display = ('name', 'parent')

admin.site.register(Product, ProductAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.unregister(Contact)
admin.site.register(ContactDetail, ContactDetailAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(District, DistrictAdmin)
admin.site.register(Facility, FacilityAdmin)

