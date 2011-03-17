#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import re
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.utils.translation import ugettext as _

from rapidsms.conf import settings
from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
from rapidsms.contrib.messagelog.models import Message
from rapidsms.contrib.messaging.utils import send_message
from logistics.apps.logistics.signals import post_save_product_report


STOCK_ON_HAND_RESPONSIBILITY = 'reporter'
REPORTEE_RESPONSIBILITY = 'reportee'
SUPERVISOR_RESPONSIBILITY = 'supervisor'
STOCK_ON_HAND_REPORT_TYPE = 'soh'
RECEIPT_REPORT_TYPE = 'rec'
REGISTER_MESSAGE = "You must registered on the Early Warning System " + \
                   "before you can submit a stock report. " + \
                   "Please contact your district administrator."
INVALID_CODE_MESSAGE = "%(code)s is/are not part of our commodity codes. "
GET_HELP_MESSAGE = "Please contact FRHP for assistance."

try:
    from settings import LOGISTICS_EMERGENCY_LEVEL_IN_MONTHS
    from settings import LOGISTICS_REORDER_LEVEL_IN_MONTHS
    from settings import LOGISTICS_MAXIMUM_LEVEL_IN_MONTHS
except ImportError:
    raise ImportError("Please define LOGISTICS_EMERGENCY_LEVEL_IN_MONTHS, " +
                      "LOGISTICS_REORDER_LEVEL_IN_MONTHS, and " +
                      "LOGISTICS_MAXIMUM_LEVEL_IN_MONTHS in your settings.py")


class Product(models.Model):
    """ e.g. oral quinine """
    name = models.CharField(max_length=100)
    units = models.CharField(max_length=100)
    sms_code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=255)
    # product code is NOT currently used. The field is there so that it can
    # be synced up with whatever internal warehousing system is used at the
    # medical facilities later
    product_code = models.CharField(max_length=100, null=True, blank=True)
    type = models.ForeignKey('ProductType')

    def __unicode__(self):
        return self.name

    @property
    def code(self):
        return self.sms_code

class ProductType(models.Model):
    """ e.g. malaria, hiv, family planning """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Product Type"

class ProductStock(models.Model):
    """
    Indicates facility-specific information about a product (such as monthly consumption rates)
    A ProductStock should exist for each product for each facility
    """
    # is_active indicates whether we are actively trying to prevent stockouts of this product
    # in practice, this means: do we bug people to report on this commodity
    # e.g. not all facilities can dispense HIV/AIDS meds, so no need to report those stock levels
    is_active = models.BooleanField(default=True)
    quantity = models.IntegerField(blank=True, null=True)
    facility = models.ForeignKey('Facility')
    product = models.ForeignKey('Product')
    days_stocked_out = models.IntegerField(default=0)
    monthly_consumption = models.IntegerField(default=None, blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('facility', 'product'),)

    def __unicode__(self):
        return "%s-%s" % (self.facility.name, self.product.name)

    @property
    def emergency_reorder_level(self):
        if self.monthly_consumption is not None:
            return int(self.monthly_consumption*settings.LOGISTICS_EMERGENCY_LEVEL_IN_MONTHS)
        return None

    @property
    def reorder_level(self):
        if self.monthly_consumption is not None:
            return int(self.monthly_consumption*settings.LOGISTICS_REORDER_LEVEL_IN_MONTHS)
        return None

    @property
    def maximum_level(self):
        if self.monthly_consumption is not None:
            return int(self.monthly_consumption*settings.LOGISTICS_MAXIMUM_LEVEL_IN_MONTHS)
        return None

    @property
    def months_remaining(self):
        if self.monthly_consumption > 0 and self.quantity is not None:
            return float(self.quantity) / float(self.monthly_consumption)
        return None

    def is_stocked_out(self):
        if self.quantity is not None:
            if self.quantity==0:
                return True
        return False

    def is_below_emergency_level(self):
        """
        Returns False if a) below emergency levels, or
        b) emergency levels not yet defined
        """
        if self.emergency_reorder_level is not None:
            if self.quantity <= self.emergency_reorder_level:
                return True
        return False

    def is_below_low_supply_but_above_emergency_level(self):
        if self.reorder_level is not None and self.emergency_reorder_level is not None:
            if self.quantity <= self.reorder_level and self.quantity> self.emergency_reorder_level:
                return True
        return False

    def is_in_good_supply(self):
        if self.maximum_level is not None and self.reorder_level is not None:
            if self.quantity > self.reorder_level and self.quantity < self.maximum_level:
                return True
        return False

    def is_overstocked(self):
        if self.maximum_level is not None:
            if self.quantity >= self.maximum_level:
                return True
        return False

class ProductReportType(models.Model):
    """ e.g. a 'stock on hand' report, or a losses&adjustments reports, or a receipt report"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Product Report Type"

class ProductReport(models.Model):
    """
     each stock on hand report or receipt submitted by a pharmacist results 
     in a unique report in the database. You can consider these as
     observations or data points.
    """
    product = models.ForeignKey(Product)
    facility = models.ForeignKey('Facility')
    report_type = models.ForeignKey(ProductReportType)
    quantity = models.IntegerField()
    report_date = models.DateTimeField(default=datetime.now)
    # message should only be null if the stock report was provided over the web
    message = models.ForeignKey(Message, blank=True, null=True)

    class Meta:
        verbose_name = "Product Report"
        ordering = ('-report_date',)

    def __unicode__(self):
        return "%s-%s-%s" % (self.facility.name, self.product.name, self.report_type.name)


class Responsibility(models.Model):
    """ e.g. 'reports stock on hand', 'orders new stock' """
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Responsibility"
        verbose_name_plural = "Responsibilities"

    def __unicode__(self):
        return _(self.name)

class ContactRole(models.Model):
    """ e.g. pharmacist, family planning nurse """
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100, blank=True)
    responsibilities = models.ManyToManyField(Responsibility, blank=True, null=True)

    class Meta:
        verbose_name = "Role"

    def __unicode__(self):
        return _(self.name)

class FacilityType(models.Model):
    """
    e.g. medical stories, district hospitals, clinics, community health centers
    """
    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True, primary_key=True)

    def __unicode__(self):
        return self.name

class Facility(models.Model):
    """
    e.g. dangme east district hospital
    """
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    type = models.ForeignKey(FacilityType)
    created_at = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=100, unique=True)
    last_reported = models.DateTimeField(default=None, blank=True, null=True)
    location = models.ForeignKey(Location)
    # i know in practice facilities are supplied by a variety of sources
    # but this relationship will only be used to enforce the idealized ordering/
    # supply relationsihp, so having a single ForeignKey mapping is sufficient
    supplied_by = models.ForeignKey('Facility', blank=True, null=True)

    def __unicode__(self):
        return self.name

    @property
    def label(self):
        return unicode(self)

    def record_consumption_by_code(self, product_code, rate):
        ps = ProductStock.objects.get(product__sms_code=product_code, facility=self)
        ps.monthly_consumption = rate
        ps.save()

    # We use 'last_reported' above instead of the following to generate reports of lateness and on-timeness.
    # This is faster and more readable, but it's duplicate data in the db, which is bad db design. Fix later?
    #@property
    #def last_reported(self):
    #    from logistics.apps.logistics.models import ProductReport, ProductStock
    #    report_count = ProductReport.objects.filter(facility=self).count()
    #    if report_count > 0:
    #        last_report = ProductReport.objects.filter(facility=self).order_by("-report_date")[0]
    #        return last_report.report_date
    #    return None

    def stockout_count(self):
        return stockout_count(facilities=[self])

    def emergency_stock_count(self):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        return emergency_stock_count(facilities=[self])

    def low_stock_count(self):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        return low_stock_count(facilities=[self])

    def good_supply_count(self):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        return good_supply_count(facilities=[self])

    def overstocked_count(self):
        return overstocked_count(facilities=[self])

    def report(self, product, report_type, quantity, message=None):
        npr = ProductReport(product=product, report_type=report_type, quantity=quantity, message=message, facility=self)
        npr.save()
        return npr

    def report_stock(self, product, quantity, message=None):
        report_type = ProductReportType.objects.get(code=STOCK_ON_HAND_REPORT_TYPE)
        return self.report(product, report_type, quantity)

    def reporters(self):
        reporters = Contact.objects.filter(facility=self)
        reporters = reporters.filter(role__responsibilities__code=STOCK_ON_HAND_RESPONSIBILITY).distinct()
        return reporters

    def reportees(self):
        reporters = Contact.objects.filter(facility=self)
        reporters = reporters.filter(role__responsibilities__code=REPORTEE_RESPONSIBILITY).distinct()
        return reporters

    def children(self):
        """
        For all intents and purses, at this time, the 'children' of a facility wrt site navigation
        are the same as the 'children' with respect to stock supply
        """
        raise Facility.objects.filter(supplied_by=self).order_by('name')

    def report_to_supervisor(self, report, kwargs, exclude=None):
        reportees = self.reportees()
        if exclude:
            reportees = reportees.exclude(pk__in=[e.pk for e in exclude])
        for reportee in reportees:
            kwargs['admin_name'] = reportee.name
            reportee.message(report % kwargs)

    def activate_product(self, product):
        ps = ProductStock.objects.get(facility=self, product=product)
        if ps.is_active == False:
            ps.is_active = True
            ps.save()

    def deactivate_product(self, product):
        ps = ProductStock.objects.get(facility=self, product=product)
        if ps.is_active == True:
            ps.is_active = False
            ps.save()

    def notify_suppliees_of_stockouts_resolved(self, stockouts_resolved, exclude=None):
        """ stockouts_resolved is a dictionary of code to product """
        to_notify = Facility.objects.filter(supplied_by=self).distinct()
        for fac in to_notify:
            reporters = fac.reporters()
            if exclude:
                reporters = reporters.exclude(pk__in=[e.pk for e in exclude])
            for reporter in reporters:
                send_message(reporter.default_connection,
                            "Dear %(name)s, %(facility)s has resolved the following stockouts: %(products)s " %
                             {'name':reporter.name,
                             'products':", ".join(stockouts_resolved),
                             'facility':self.name})

class ProductReportsHelper(object):
    """
    The following is a helper class (doesn't touch the db) which takes in aggregate
    sets of reports and handles things like string parsing, aggregate validation,
    lazy UPDATE-ing, error reporting etc.
    """
    REC_SEPARATOR = '-'

    def __init__(self, sdp, report_type, message=None):
        self.product_stock = {}
        self.consumption = {}
        self.product_received = {}
        if sdp is None:
            raise ValueError("Unknown Facility.")
        self.facility = sdp
        self.message = message
        self.has_stockout = False
        self.report_type = report_type
        self.errors = []

    def _clean_string(self, string):
        if not string:
            return string
        mylist = list(string)
        newstring = string[0]
        i = 1
        while i < len(mylist)-1:
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
        if not string:
            return
        match = re.search("[0-9]",string)
        if not match:
            raise ValueError("Stock report should contain quantity of stock on hand. " + \
                             "Please contact FRHP for assistance.")
        string = self._clean_string(string)
        an_iter = self._getTokens(string)
        commodity = None
        while True:
            try:
                while commodity is None or not commodity.isalpha():
                    commodity = an_iter.next()
                count = an_iter.next()
                while not count.isdigit():
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
        if self.errors:
            self.errors.append(GET_HELP_MESSAGE)
        return

    def save(self):
        stockouts_resolved = []
        for stock_code in self.product_stock:
            try:
                original_quantity = ProductStock.objects.get(facility=self.facility, product__sms_code=stock_code).quantity
            except ProductStock.DoesNotExist:
                original_quantity = 0
            new_quantity = self.product_stock[stock_code]
            self._record_product_report_by_code(stock_code, new_quantity, self.report_type)
            if original_quantity == 0 and new_quantity > 0:
                stockouts_resolved.append(stock_code)
        if stockouts_resolved:
            # notify all facilities supplied by this one
            # this needs to be decoupled more; could pull it out into a signal
            if self.message:
                self.facility.notify_suppliees_of_stockouts_resolved(stockouts_resolved, 
                                                                     exclude=[self.message.contact])
            else:
                self.facility.notify_suppliees_of_stockouts_resolved(stockouts_resolved)
        for stock_code in self.consumption:
            self.facility.record_consumption_by_code(stock_code, self.consumption[stock_code])
        for stock_code in self.product_received:
            self._record_product_report_by_code(stock_code, self.product_received[stock_code], RECEIPT_REPORT_TYPE)

    def add_product_consumption(self, product, consumption):
        if isinstance(consumption, basestring) and consumption.isdigit():
            consumption = int(consumption)
        if not isinstance(consumption, int):
            raise TypeError("Consumption must be reported in integers")
        self.consumption[product.sms_code] = consumption

    def add_product_stock(self, product_code, stock, save=False, consumption=None):
        if isinstance(stock, basestring) and stock.isdigit():
            stock = int(stock)
        if not isinstance(stock, int):
            raise TypeError("Stock must be reported in integers")
        try:
            product = Product.objects.get(sms_code__icontains=product_code)
        except (Product.DoesNotExist, Product.MultipleObjectsReturned):
            raise ValueError(_(INVALID_CODE_MESSAGE) % {'code':product_code.upper()})
        if save:
            self._record_product_report(product, stock, self.report_type)
        self.product_stock[product_code] = stock
        if consumption is not None:
            self.consumption[product_code] = consumption
        if stock == 0:
            self.has_stockout = True

    def _record_product_report_by_code(self, product_code, quantity, report_type):
        try:
            product = Product.objects.get(sms_code__icontains=product_code)
        except Product.DoesNotExist, Product.MultipleObjectsReturned:
            raise ValueError(_(INVALID_CODE_MESSAGE) % {'code':product_code.upper() })
        self._record_product_report(product, quantity, report_type)

    def _record_product_report(self, product, quantity, report_type):
        report_type = ProductReportType.objects.get(code=report_type)
        self.facility.report(product=product, report_type=report_type,
                             quantity=quantity, message=self.message)

    def _record_product_stock(self, product_code, quantity):
        self._record_product_report(product_code, quantity, STOCK_ON_HAND_REPORT_TYPE)

    def _record_product_receipt(self, product, quantity):
        self._record_product_report(product, quantity, RECEIPT_REPORT_TYPE)

    def add_product_receipt(self, product_code, quantity, save=True):
        if isinstance(quantity, basestring) and quantity.isdigit():
            quantity = int(quantity)
        if not isinstance(quantity, int):
            raise TypeError("stock must be reported in integers")
        try:
            product = Product.objects.get(sms_code__icontains=product_code)
        except Product.DoesNotExist, Product.MultipleObjectsReturned:
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
            productstock = ProductStock.objects.filter(facility=self.facility).get(product__sms_code__icontains=i)
            #if productstock.monthly_consumption == 0:
            #    raise ValueError("I'm sorry. I cannot calculate low
            #    supply for %(code)s until I know your monthly consumption.
            #    Please contact FRHP for assistance." % {'code':i})
            if productstock.monthly_consumption is not None:
                if self.product_stock[i] <= productstock.monthly_consumption*settings.LOGISTICS_REORDER_LEVEL_IN_MONTHS and \
                   self.product_stock[i] != 0:
                    low_supply = "%s %s" % (low_supply, i)
        low_supply = low_supply.strip()
        return low_supply

    def over_supply(self):
        over_supply = ""
        for i in self.product_stock:
            productstock = ProductStock.objects.filter(facility=self.facility).get(product__sms_code__icontains=i)
            #if productstock.monthly_consumption == 0:
            #    raise ValueError("I'm sorry. I cannot calculate oversupply
            #    for %(code)s until I know your monthly con/sumption.
            #    Please contact FRHP for assistance." % {'code':i})
            if productstock.monthly_consumption is not None:
                if self.product_stock[i] >= productstock.monthly_consumption*settings.LOGISTICS_MAXIMUM_LEVEL_IN_MONTHS and \
                   productstock.monthly_consumption>0:
                    over_supply = "%s %s" % (over_supply, i)
        over_supply = over_supply.strip()
        return over_supply

    def missing_products(self):
        """
        check for active products that haven't yet been added
        to this stockreport helper
        """
        all_products = []
        date_check = datetime.now() + relativedelta(days=-7)
        reporter = self.message.contact
        
        missing_products = Product.objects.filter(Q(productstock__facility=self.facility,
                                                    productstock__product__reported_by=reporter),
                                                  ~Q(productreport__report_date__gt=date_check) )
        for dict in missing_products.values('sms_code'):
            all_products.append(dict['sms_code'])
        return list(set(all_products)-self.reported_products())

    def get_responses(self):
        response = ''
        super_response = ''
        stockouts = self.stockouts()
        low_supply = self.low_supply()
        over_supply = self.over_supply()
        received = self.received_products()
        missing_product_list = self.missing_products()
        if self.has_stockout:
            response = response + 'the following items are stocked out: %(stockouts)s. '
            super_response = "stockouts %(stockouts)s; "
        if low_supply:
            response = response + 'the following items need to be reordered: %(low_supply)s. '
            super_response = super_response + "below reorder level %(low_supply)s; "
        if self.has_stockout or low_supply:
            response = response + 'Please place an order now. '
        if missing_product_list:
            if not response:
                response = response + 'thank you for reporting your stock on hand. '
            response = response + 'Still missing %(missing_stock)s. '
        if over_supply:
            super_response = super_response + "overstocked %(overstocked)s; "
            if not response:
                response = 'the following items are overstocked: %(overstocked)s. The district admin has been informed.'
        if not response:
            if received:
                response = 'thank you for reporting the commodities you have. You received %(received)s.'
            else:
                response = 'thank you for reporting the commodities you have in stock.'
        response = 'Dear %(name)s, ' + response.strip()
        if super_response:
            super_response = 'Dear %(admin_name)s, %(facility)s is experiencing the following problems: ' + super_response.strip().strip(';')
        kwargs = {  'low_supply': low_supply,
                    'stockouts': stockouts,
                    'missing_stock': ', '.join(missing_product_list),
                    'stocks': self.all(),
                    'received': self.received(),
                    'overstocked': over_supply,
                    'name': self.message.contact.name,
                    'facility': self.facility.name }
        return (response, super_response, kwargs)

def get_geography():
    """
    to get a sense of the complete geography in the system
    we return the top-level entities (example regions)
    which we can easily iterate through, using children()
    in order to assess the whole geography that we're handling
    """
    try:
        return Location.objects.get(code=settings.COUNTRY)
    except ValueError:
        raise ValueError("Invalid COUNTRY defined in settings.py. Please choose one that matches the code of a registered location.")
    except Location.MultipleObjectsReturned:
        raise Location.MultipleObjectsReturned("You must define only one root location (no parent id) per site.")
    except Location.DoesNotExist:
        raise Location.MultipleObjectsReturned("The COUNTRY specified in settings.py does not exist.")

post_save.connect(post_save_product_report, sender=ProductReport)

def _filtered_stock(product, producttype):
    results = ProductStock.objects.all()
    if product is not None:
        results = results.filter(product=product)
    elif producttype is not None:
        results = results.filter(product__type=producttype)
    return results

def stockout_count(facilities=None, product=None, producttype=None):
    results = _filtered_stock(product, producttype).filter(facility__in=facilities).filter(quantity=0)
    return results.count()

def emergency_stock_count(facilities=None, product=None, producttype=None):
    """ This indicates all stock below reorder levels,
        including all stock below emergency supply levels
    """
    emergency_stock = 0
    stocks = _filtered_stock(product, producttype).filter(facility__in=facilities).filter(quantity__gt=0)
    for stock in stocks:
        if stock.is_below_emergency_level():
            emergency_stock = emergency_stock + 1
    return emergency_stock

def low_stock_count(facilities=None, product=None, producttype=None):
    """ This indicates all stock below reorder levels,
        including all stock below emergency supply levels
    """
    low_stock_count = 0
    stocks = _filtered_stock(product, producttype).filter(facility__in=facilities).filter(quantity__gt=0)
    for stock in stocks:
        if stock.is_below_low_supply_but_above_emergency_level():
            low_stock_count = low_stock_count + 1
    return low_stock_count

def good_supply_count(facilities=None, product=None, producttype=None):
    """ This indicates all stock below reorder levels,
        including all stock below emergency supply levels
    """
    good_supply_count = 0
    stocks = _filtered_stock(product, producttype).filter(facility__in=facilities).filter(quantity__gt=0)
    for stock in stocks:
        if stock.is_in_good_supply():
            good_supply_count = good_supply_count + 1
    return good_supply_count

def overstocked_count(facilities=None, product=None, producttype=None):
    overstock_count = 0
    stocks = _filtered_stock(product, producttype).filter(facility__in=facilities).filter(quantity__gt=0)
    for stock in stocks:
        if stock.is_overstocked():
            overstock_count = overstock_count + 1
    return overstock_count


