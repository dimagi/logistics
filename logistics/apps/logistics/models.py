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
SUPERVISOR_RESPONSIBILITY = 'supervisor'

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

    def parentsdp(self):
        return ServiceDeliveryPoint(self.parent)

    def supervisor_report(self, stock_report):
        sdp = self.parentsdp()
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
    monthly_consumption = models.IntegerField(default=0)
    last_modified = models.DateTimeField(auto_now=True)

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

    def supervisor(self):
        """
        If this contact is not a supervisor, message all staff with a supervisor responsibility at this facility
        If this contact is a supervisor, message the super at the next facility up
        Question: this looks like business/controller logic. Should it really be in 'model' code?
        """

        if SUPERVISOR not in self.role.responsibilities.objects.all():
            return LogisticsContact.objects.filter(service_delivery_point=self.service_delivery_point,
                                                   role=SUPERVISOR)
        return LogisticsContact.objects.filter(service_delivery_point=self.service_delivery_point.parentsdp(),
                                               role=SUPERVISOR)

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

class ProductStockReport(object):
    """ The following is a helper class to make it easy to generate reports based on stock on hand """
    def __init__(self, sdp, message):
        self.product_stock = {}
        self.product_received = {}
        self.facility = sdp
        self.message = message
        self.has_stockout = False

    def parse(self, string):
        my_list = string.split()

        def getTokens(seq):
            for item in seq:
                yield item
        an_iter = getTokens(my_list)
        a = None
        try:
            while True:
                if a is None:
                    a = an_iter.next()
                b = an_iter.next()
                self.add_product_stock(a,b)
                c = an_iter.next()
                if c.isdigit():
                    self.add_product_receipt(a,c)
                    a = None
                else:
                    a = c
        except StopIteration:
            pass
        return

    def add_product_stock(self, product, stock, save=True):
        if isinstance(stock, basestring) and stock.isdigit():
            stock = int(stock)
        if not isinstance(stock,int):
            raise TypeError("stock must be reported in integers")
        stock = int(stock)
        self.product_stock[product] = stock
        if stock == 0:
            self.has_stockout = True
        if save:
            self._record_product_stock(product, stock)

    def _record_product_report(self, product_code, quantity, report_type):
        try:
            product = Product.objects.get(sms_code__contains=product_code)
        except Product.DoesNotExist:
            raise ValueError(_("Sorry, invalid product code %(code)s"), code=product_code.upper())
        self.facility.report(product=product, report_type=report_type,
                             quantity=quantity, message=self.message)


    def _record_product_stock(self, product_code, quantity):
        report_type = ProductReportType.objects.get(slug='soh')
        self._record_product_report(product_code, quantity, report_type)

    def _record_product_receipt(self, product_code, quantity):
        report_type = ProductReportType.objects.get(slug='rec')
        self._record_product_report(product_code, quantity, report_type)

    def add_product_receipt(self, product, quantity, save=True):
        if isinstance(quantity, basestring) and quantity.isdigit():
            quantity = int(quantity)
        if not isinstance(quantity,int):
            raise TypeError("stock must be reported in integers")
        self.product_received[product] = quantity
        self._record_product_receipt(product, quantity)

    def reported_products(self):
        reported_products = []
        for i in self.product_stock:    
            reported_products.append(i)
        return set(reported_products)

    def received_products(self):
        received_products = []
        for i in self.product_received:
            received_products.append(i)
        return set(received_products)

    def all(self):
        reply_list = []
        for i in self.product_stock:
            reply_list.append('%s %s' % (i, self.product_stock[i]))
        return ', '.join(reply_list)

    def received(self):
        reply_list = []
        for i in self.product_received:
            reply_list.append('%s %s' % (i, self.product_received[i]))
        return ', '.join(reply_list)

    def stockouts(self):
        stocked_out = ""
        for i in self.product_stock:
            if self.product_stock[i] == 0:
                stocked_out = "%s %s" % (stocked_out, i)
        stocked_out = stocked_out.strip()
        return stocked_out

    def low_supply(self):
        self.facility
        low_supply = ""
        for i in self.product_stock:
            productstock = ProductStock.objects.filter(service_delivery_point=self.facility).get(product__sms_code__contains=i)
            if self.product_stock[i] < productstock.monthly_consumption:
                low_supply = "%s %s" % (low_supply, i)
        low_supply = low_supply.strip()
        return low_supply

    def over_supply(self):
        return NotImplementedError
