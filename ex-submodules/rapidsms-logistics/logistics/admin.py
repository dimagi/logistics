#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from logistics.models import *
from rapidsms.models import Contact as RapidSMSContact

class LogisticsProfileAdmin(admin.ModelAdmin):
    model = LogisticsProfile

class ContactRoleAdmin(admin.ModelAdmin):
    model = ContactRole

class ResponsibilityAdmin(admin.ModelAdmin):
    model = Responsibility

class ProductAdmin(admin.ModelAdmin):
    model = Product
    list_display = ('name', 'units', 'sms_code', 'description', 'product_code', 'type')

class ProductTypeAdmin(admin.ModelAdmin):
    model = ProductType

class ProductStockAdmin(admin.ModelAdmin):
    model = ProductStock
    list_display = ('supply_point', 'product', 'is_active', 'quantity','auto_monthly_consumption')
    list_filter = ('product', 'is_active', 'auto_monthly_consumption')

class ProductReportAdmin(admin.ModelAdmin):
    model = ProductReport
    list_display = ('product', 'supply_point', 'report_type', 'quantity','report_date', 'message')
    list_filter = ('product', 'supply_point', 'report_type')

class ProductReportTypeAdmin(admin.ModelAdmin):
    model = ProductReportType

class RequisitionReportAdmin(admin.ModelAdmin):
    model = RequisitionReport
    
class SupplyPointTypeAdmin(admin.ModelAdmin):
    model = SupplyPointType

class DefaultMonthlyConsumptionAdmin(admin.ModelAdmin):
    model = DefaultMonthlyConsumption
    list_display = ('product', 'supply_point_type', 'default_monthly_consumption')
    list_filter = ('product', 'supply_point_type')

class SupplyPointAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "type")
    list_filter = ('type', 'active')
    search_fields = ('code',)
    model = SupplyPoint

class StockRequestAdmin(admin.ModelAdmin):
    model = StockRequest
    list_display = ('product', 'supply_point', 'status', 'requested_on','amount_requested', 'amount_approved', 'amount_received')
    list_filter = ('product', 'supply_point', 'status')

class StockTransactionAdmin(admin.ModelAdmin):
    model = StockTransaction
    
    list_display = ('product', 'supply_point', 'date', 'quantity','beginning_balance', 'ending_balance')
    list_filter = ('product', 'supply_point')

class LogisticsContactAdmin(admin.ModelAdmin):
    model = Contact
    list_display = ('name', 'supply_point', 'role', 'is_active')

class NagRecordAdmin(admin.ModelAdmin):
    model = NagRecord
    list_display = ("supply_point", "report_date", "warning", "nag_type")
    list_filter = ("supply_point", "warning", "nag_type")

class HistoricalStockCacheAdmin(admin.ModelAdmin):
    model = HistoricalStockCache
    list_display = ("supply_point", "product", "year", "month", "stock")
    list_filter = ("supply_point", "product", "year", "month")

class SupplyPointWarehouseRecordAdmin(admin.ModelAdmin):
    model = SupplyPointWarehouseRecord
    list_display = ("supply_point", "create_date")
    list_filter = ("create_date",)


admin.site.unregister(Contact)
admin.site.register(Contact, LogisticsContactAdmin)

admin.site.register(LogisticsProfile, LogisticsProfileAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductType, ProductTypeAdmin)
admin.site.register(ProductStock, ProductStockAdmin)
admin.site.register(ProductReport, ProductReportAdmin)
admin.site.register(RequisitionReport, RequisitionReportAdmin)
admin.site.register(ProductReportType, ProductReportTypeAdmin)
admin.site.register(StockTransaction, StockTransactionAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(Responsibility, ResponsibilityAdmin)
admin.site.register(SupplyPointType, SupplyPointTypeAdmin)
admin.site.register(SupplyPoint, SupplyPointAdmin)
admin.site.register(StockRequest, StockRequestAdmin)
admin.site.register(NagRecord, NagRecordAdmin)
admin.site.register(DefaultMonthlyConsumption, DefaultMonthlyConsumptionAdmin)
admin.site.register(HistoricalStockCache, HistoricalStockCacheAdmin)
admin.site.register(SupplyPointWarehouseRecord, SupplyPointWarehouseRecordAdmin)
