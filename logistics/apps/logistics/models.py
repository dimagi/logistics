#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import logging
from re import match
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, Max
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _

from rapidsms.models import ExtensibleModelBase
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact as RapidSMSContact
from rapidsms.models import Connection
from rapidsms.contrib.messagelog.models import Message

STOCK_ON_HAND_RESPONSIBILITY = 'reporter'
REPORTEE_RESPONSIBILITY = 'reportee'

class ServiceDeliveryPointType(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

class ServiceDeliveryPoint(Location):
    """
    ServiceDeliveryPoint - the main concept of a location.  Currently covers MOHSW, Regions, Districts and Facilities.
    This could/should be broken out into subclasses.
    """
    @property
    def label(self):
        return unicode(self)

    name = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    msd_code = models.CharField(max_length=100, blank=True, null=True)
    service_delivery_point_type = models.ForeignKey(ServiceDeliveryPointType)

    def report(self, **kwargs):
        npr = ProductReport(service_delivery_point = self,  **kwargs)
        npr.save()

    def reporters(self):
        reporters = LogisticsContact.objects.filter(service_delivery_point=self)
        reporters = LogisticsContact.objects.filter(role__responsibilities__slug=STOCK_ON_HAND_RESPONSIBILITY).distinct()
        return reporters

    def reportees(self):
        reporters = LogisticsContact.objects.filter(service_delivery_point=self)
        reporters = LogisticsContact.objects.filter(role__responsibilities__slug=REPORTEE_RESPONSIBILITY).distinct()
        return reporters

    def supervisor_report(self, stock_report):
        sdp = ServiceDeliveryPoint(self.parent)
        reportees = sdp.reportees()
        stockouts = stock_report.stockouts()
        if stockouts:
            for reportee in reportees:
                reportee.message(_('You have stockouts: %(stockouts)s'), {'stockouts':stockouts})
        low_supply = stock_report.low_supply()
        if low_supply:
            for reportee in reportees:
                reportee.message(_('You have low_supply: %(low_supply)s'), {'low_supply':low_supply})
        over_supply = stock_report.over_supply()
        if over_supply:
            for reportee in reportees:
                reportee.message(_('You have over_supply: %(over_supply)s'), {'over_supply':over_supply})

class Product(models.Model):
    name = models.CharField(max_length=100)
    units = models.CharField(max_length=100)
    sms_code = models.CharField(max_length=10)
    description = models.CharField(max_length=255)
    product_code = models.CharField(max_length=100, null=True, blank=True)
    
    def __unicode__(self):
        return self.name
    
class ProductStock(models.Model):
    is_active = models.BooleanField(default=True)
    quantity = models.IntegerField(blank=True, null=True)
    service_delivery_point = models.ForeignKey('ServiceDeliveryPoint')
    product = models.ForeignKey('Product')
    days_stocked_out = models.IntegerField(default=0)
    daily_consumption_rate = models.IntegerField(default=0)

    def __unicode__(self):
        return "%s-%s" % (self.service_delivery_point.name, self.product.name)

class Responsibility(models.Model):
    slug = models.CharField(max_length=30, blank=True)
    name = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Responsibility"
        verbose_name_plural = "Responsibilities"

    def __unicode__(self):
        return _(self.name)

class ContactRole(models.Model):
    slug = models.CharField(max_length=30, blank=True)
    name = models.CharField(max_length=100, blank=True)
    responsibilities = models.ManyToManyField(Responsibility, blank=True, null=True)

    class Meta:
        verbose_name = "Role"

    def __unicode__(self):
        return _(self.name)
    
class LogisticsContact(RapidSMSContact):
    role = models.ForeignKey(ContactRole, null=True, blank=True)
    service_delivery_point = models.ForeignKey(ServiceDeliveryPoint,null=True,blank=True)
    needs_reminders = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Contact Detail"

    def __unicode__(self):
        return self.name

    @property
    def phone(self):
        if self.default_connection:
            return self.default_connection.identity
        else:
            return " "

class ProductReportType(models.Model):
    """ e.g. a 'stock on hand' report, or a losses&adjustments reports, or a receipt report"""
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=10)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Product Report Type"

class ProductReport(models.Model):
    product = models.ForeignKey(Product)
    service_delivery_point = models.ForeignKey(ServiceDeliveryPoint)
    report_type = models.ForeignKey(ProductReportType)
    quantity = models.IntegerField()
    report_date = models.DateTimeField(default=datetime.now)
    message = models.ForeignKey(Message)

    class Meta:
        verbose_name = "Product Report"
        ordering = ('-report_date',)

    def __unicode__(self):
        return "%s-%s-%s" % (self.service_delivery_point.name, self.product.name, self.report_type.name)

