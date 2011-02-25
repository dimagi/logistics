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
from rapidsms.models import Contact
from rapidsms.models import Connection
from rapidsms.contrib.messagelog.models import Message
from rapidsms.contrib.locations.models import Location, LocationType

STOCK_ON_HAND_REPORT_TYPE = 'soh'
RECEIPT_REPORT_TYPE = 'rec'
REGISTER_MESSAGE = "You must registered on the Early Warning System before you can submit a stock report. Please contact your district administrator."
INVALID_CODE_MESSAGE = "%(code)s is/are not part of our commodity codes. Please contact FRHP for assistance."

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
    location = models.ForeignKey(Location)
    product = models.ForeignKey('Product')
    days_stocked_out = models.IntegerField(default=0)
    monthly_consumption = models.IntegerField(default=0)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "%s-%s" % (self.location.name, self.product.name)

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
    location = models.ForeignKey(Location)
    report_type = models.ForeignKey(ProductReportType)
    quantity = models.IntegerField()
    report_date = models.DateTimeField(default=datetime.now)
    # message should only be null if the stock report was provided over the web
    message = models.ForeignKey(Message, blank=True, null=True)

    class Meta:
        verbose_name = "Product Report"
        ordering = ('-report_date',)

    def __unicode__(self):
        return "%s-%s-%s" % (self.location.name, self.product.name, self.report_type.name)

class ProductStockReport(object):
    REC_SEPARATOR = '-'

    """ The following is a helper class to make it easy to generate reports based on stock on hand """
    def __init__(self, sdp, report_type, message=None):
        self.product_stock = {}
        self.product_received = {}
        self.facility = sdp
        self.message = message
        self.has_stockout = False
        self.report_type = report_type
        self.errors = []

    def _clean_string(self, string):
        mylist = list(string)
        newstring = string[0]
        i = 1
        while i<len(mylist)-1:
            if mylist[i] == ' ' and mylist[i-1].isdigit() and mylist[i+1].isdigit():
                newstring = newstring + self.REC_SEPARATOR
            else:
                newstring = newstring + mylist[i]
            i = i + 1
        newstring = newstring + string[-1]
        string = newstring

        string = string.replace(' ','')
        separators = [',', '/', ';', '*', '+', '-']
        for mark in separators:
                string = string.replace(mark, self.REC_SEPARATOR)
        junk = ['\'', '\"', '`', '(', ')']
        for mark in junk:
            string = string.replace(mark, '')
        return string.lower()

    def _getTokens(self, string):
        mylist = list(string)
        token = ''
        i = 0
        while i<len(mylist):
            token = token + mylist[i]
            if i+1 == len(mylist):
                # you've reached the end
                yield token
            elif mylist[i].isdigit() and not mylist[i+1].isdigit() or \
                mylist[i].isalpha() and not mylist[i+1].isalpha() or \
                not mylist[i].isalnum() and mylist[i+1].isalnum():
                    yield token
                    token = ''
            i = i+1

    def parse(self, string):
        string = self._clean_string(string)
        an_iter = self._getTokens(string)
        commodity = None
        while True:
            try:
                    if commodity is None:
                        commodity = an_iter.next()
                    count = an_iter.next()
                    self.add_product_stock(commodity, count)
                    token_a = an_iter.next()
                    if not token_a.isalnum():
                        token_b = an_iter.next()
                        while not token_b.isalnum():
                            token_b = an_iter.next()
                        if token_b.isdigit():
                            # if digit, then the user is reporting receipts
                            self.add_product_receipt(commodity, token_b)
                            commodity = None
                        else:
                            # if alpha, user is reporting soh, so loop
                            commodity = token_b
                    else:
                        commodity = token_a
            except ValueError, e:
                self.errors.append(e)
                commodity = None
                continue
            except StopIteration:
                break
        self.save()
        return

    def save(self):
        for stock_code in self.product_stock:
            try:
                product = Product.objects.get(sms_code__icontains=stock_code)
            except Product.DoesNotExist:
                raise ValueError(_(INVALID_CODE_MESSAGE) % {'code':stock_code.upper() })
            self._record_product_report(product, self.product_stock[stock_code], self.report_type)
        for stock_code in self.product_received:
            try:
                product = Product.objects.get(sms_code__icontains=stock_code)
            except Product.DoesNotExist:
                raise ValueError(_(INVALID_CODE_MESSAGE) % {'code':stock_code.upper()})
            self._record_product_report(product, self.product_received[stock_code], RECEIPT_REPORT_TYPE)

    def add_product_stock(self, product_code, stock, save=False):
        if isinstance(stock, basestring) and stock.isdigit():
            stock = int(stock)
        if not isinstance(stock,int):
            raise TypeError("Stock must be reported in integers")
        stock = int(stock)
        try:
            product = Product.objects.get(sms_code__icontains=product_code)
        except Product.DoesNotExist:
            raise ValueError(_(INVALID_CODE_MESSAGE) % {'code':product_code.upper()})
        if save:
            self._record_product_report(product, stock, self.report_type)
        self.product_stock[product_code] = stock
        if stock == 0:
            self.has_stockout = True

    def _record_product_report(self, product, quantity, report_type):
        report_type = ProductReportType.objects.get(slug=report_type)
        self.facility.report(product=product, report_type=report_type,
                             quantity=quantity, message=self.message)

    def _record_product_stock(self, product_code, quantity):
        self._record_product_report(product_code, quantity, STOCK_ON_HAND_REPORT_TYPE)

    def _record_product_receipt(self, product, quantity):
        self._record_product_report(product, quantity, RECEIPT_REPORT_TYPE)

    def add_product_receipt(self, product_code, quantity, save=True):
        if isinstance(quantity, basestring) and quantity.isdigit():
            quantity = int(quantity)
        if not isinstance(quantity,int):
            raise TypeError("stock must be reported in integers")
        try:
            product = Product.objects.get(sms_code__icontains=product_code)
        except Product.DoesNotExist:
            raise ValueError(_(INVALID_CODE_MESSAGE) % {'code':product_code.upper()})
        self.product_received[product_code] = quantity
        if save:
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
        low_supply = ""
        for i in self.product_stock:
            productstock = ProductStock.objects.filter(location=self.facility).get(product__sms_code__icontains=i)
            #if productstock.monthly_consumption == 0:
            #    raise ValueError("I'm sorry. I cannot calculate low supply for %(code)s until I know your monthly consumption. Please contact FRHP for assistance." % {'code':i})
            if self.product_stock[i] < productstock.monthly_consumption and self.product_stock[i] != 0 and productstock.monthly_consumption>0:
                low_supply = "%s %s" % (low_supply, i)
        low_supply = low_supply.strip()
        return low_supply

    def over_supply(self):
        over_supply = ""
        for i in self.product_stock:
            productstock = ProductStock.objects.filter(location=self.facility).get(product__sms_code__icontains=i)
            #if productstock.monthly_consumption == 0:
            #    raise ValueError("I'm sorry. I cannot calculate oversupply for %(code)s until I know your monthly consumption. Please contact FRHP for assistance." % {'code':i})
            if self.product_stock[i] > productstock.monthly_consumption*3 and productstock.monthly_consumption>0:
                over_supply = "%s %s" % (over_supply, i)
        over_supply = over_supply.strip()
        return over_supply
