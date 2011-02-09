#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from logistics.apps.logistics.models import *
from rapidsms.models import Contact as RapidSMSContact

class ConnectionInline(admin.TabularInline):
    model = Connection
    extra = 1

class LogisticsContactAdmin(admin.ModelAdmin):
    model = LogisticsContact
    list_display = ('name', 'role', 'service_delivery_point')
    inlines = [
        ConnectionInline,
    ]

class ContactRoleAdmin(admin.ModelAdmin):
    model = ContactRole

class ResponsibilityAdmin(admin.ModelAdmin):
    model = Responsibility

class ProductAdmin(admin.ModelAdmin):
    model = Product
    list_display = ('name', 'units', 'sms_code', 'description','product_code')

class ProductReportAdmin(admin.ModelAdmin):
    model = ProductReport

class ProductReportTypeAdmin(admin.ModelAdmin):
    model = ProductReportType

class ServiceDeliveryPointAdmin(admin.ModelAdmin):
    model = ServiceDeliveryPoint

class ServiceDeliveryPointTypeAdmin(admin.ModelAdmin):
    model = ServiceDeliveryPointType

admin.site.register(Product, ProductAdmin)
admin.site.register(ProductReport, ProductReportAdmin)
admin.site.register(ProductReportType, ProductReportTypeAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(Responsibility, ResponsibilityAdmin)
admin.site.unregister(RapidSMSContact)
admin.site.register(LogisticsContact, LogisticsContactAdmin)
admin.site.register(ServiceDeliveryPoint, ServiceDeliveryPointAdmin)
admin.site.register(ServiceDeliveryPointType, ServiceDeliveryPointTypeAdmin)

