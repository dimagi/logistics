#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from logistics.apps.logistics.models import *
from rapidsms.models import Contact as RapidSMSContact

class LogisticsProfileAdmin(admin.ModelAdmin):
    model = LogisticsProfile

class ContactRoleAdmin(admin.ModelAdmin):
    model = ContactRole

class ResponsibilityAdmin(admin.ModelAdmin):
    model = Responsibility

class ProductAdmin(admin.ModelAdmin):
    model = Product
    list_display = ('name', 'units', 'sms_code', 'description','product_code')

class ProductTypeAdmin(admin.ModelAdmin):
    model = ProductType

class ProductStockAdmin(admin.ModelAdmin):
    model = ProductStock

class ProductReportAdmin(admin.ModelAdmin):
    model = ProductReport

class ProductReportTypeAdmin(admin.ModelAdmin):
    model = ProductReportType

class FacilityAdmin(admin.ModelAdmin):
    model = Facility

class FacilityTypeAdmin(admin.ModelAdmin):
    model = FacilityType

admin.site.register(LogisticsProfile, LogisticsProfileAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductType, ProductTypeAdmin)
admin.site.register(ProductStock, ProductStockAdmin)
admin.site.register(ProductReport, ProductReportAdmin)
admin.site.register(ProductReportType, ProductReportTypeAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(Responsibility, ResponsibilityAdmin)
admin.site.register(FacilityType, FacilityTypeAdmin)
admin.site.register(Facility, FacilityAdmin)

