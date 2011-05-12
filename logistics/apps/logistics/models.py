#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import re
import math
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, Sum
from django.db.models.signals import post_save
from django.utils.translation import ugettext as _

from rapidsms.conf import settings
from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
from rapidsms.contrib.messagelog.models import Message
from rapidsms.contrib.messaging.utils import send_message
from logistics.apps.logistics.signals import post_save_product_report, create_user_profile,\
    stockout_resolved
from logistics.apps.logistics.errors import *
from django.db.models.fields import PositiveIntegerField
import uuid
from logistics.apps.logistics.const import Reports
#import logistics.apps.logistics.log


STOCK_ON_HAND_RESPONSIBILITY = 'reporter'
REPORTEE_RESPONSIBILITY = 'reportee'
STOCK_ON_HAND_REPORT_TYPE = 'soh'
RECEIPT_REPORT_TYPE = 'rec'
REGISTER_MESSAGE = "You must registered on EWS " + \
                   "before you can submit a stock report. " + \
                   "Please contact your DHIO."
INVALID_CODE_MESSAGE = "%(code)s is/are not part of our commodity codes. "
GET_HELP_MESSAGE = " Please contact your DHIO for assistance."
DISTRICT_TYPE = 'district'
CHPS_TYPE = 'chps'


try:
    from settings import LOGISTICS_EMERGENCY_LEVEL_IN_MONTHS
    from settings import LOGISTICS_REORDER_LEVEL_IN_MONTHS
    from settings import LOGISTICS_MAXIMUM_LEVEL_IN_MONTHS
except ImportError:
    raise ImportError("Please define LOGISTICS_EMERGENCY_LEVEL_IN_MONTHS, " +
                      "LOGISTICS_REORDER_LEVEL_IN_MONTHS, and " +
                      "LOGISTICS_MAXIMUM_LEVEL_IN_MONTHS in your settings.py")

class LogisticsProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    location = models.ForeignKey(Location, blank=True, null=True)
    facility = models.ForeignKey('Facility', blank=True, null=True)

    def __unicode__(self):
        return "%s (%s, %s)" % (self.user.username, self.location, self.facility)

post_save.connect(create_user_profile, sender=User)

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
    average_monthly_consumption = PositiveIntegerField(null=True, blank=True)
    type = models.ForeignKey('ProductType')

    def __unicode__(self):
        return self.name

    @property
    def code(self):
        return self.sms_code
    
    @classmethod
    def by_code(cls, code):
        return cls.objects.get(sms_code=code)

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
    Indicates supply point-specific information about a product (such as monthly consumption rates)
    A ProductStock should exist for each product for each supply point
    """
    # is_active indicates whether we are actively trying to prevent stockouts of this product
    # in practice, this means: do we bug people to report on this commodity
    # e.g. not all facilities can dispense HIV/AIDS meds, so no need to report those stock levels
    is_active = models.BooleanField(default=True)
    supply_point = models.ForeignKey('SupplyPoint')
    quantity = models.IntegerField(blank=True, null=True)
    product = models.ForeignKey('Product')
    days_stocked_out = models.IntegerField(default=0)
    base_monthly_consumption = models.PositiveIntegerField(default=None, blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('supply_point', 'product'),)

    def __unicode__(self):
        return "%s-%s" % (self.supply_point.name, self.product.name)

    @property
    def monthly_consumption(self):
        d = self.daily_consumption
        if d is None:
            if self.base_monthly_consumption is not None:
                return self.base_monthly_consumption
            elif self.product.average_monthly_consumption is not None:
                return self.product.average_monthly_consumption
            return None

        return d * 30

    @monthly_consumption.setter
    def monthly_consumption(self,value):
        self.base_monthly_consumption = value

    @property
    def daily_consumption(self):
        trans = StockTransaction.objects.filter(supply_point=self.supply_point,
                                                product=self.product).order_by('date')
        if len(trans) < 2:
            # not enough data
            return None
        quantity = 0
        days = 0
        prior = trans[0]
        for tr in trans[1:]:
            if tr.quantity < 0: # consumption
                quantity -= tr.quantity # negative number
                delta = tr.date - prior.date
                days += delta.days
            prior = tr
        if days < settings.LOGISTICS_MINIMUM_DAYS_TO_CALCULATE_CONSUMPTION:
            return None
        return quantity / days

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
        if self.monthly_consumption is not None and self.monthly_consumption > 0 \
          and self.quantity is not None:
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
            if self.quantity > self.maximum_level:
                return True
        return False

class StockTransferStatus(object):
    """Basically a const for our choices"""
    INITIATED = "initiated"
    CONFIRMED = "confirmed"
    CANCELED = "canceled"
    CHOICES = [INITIATED, CONFIRMED, CANCELED] 
    STATUS_CHOICES = ((val, val) for val in CHOICES)
        
class StockTransfer(models.Model):
    """
    Transfers can be made between supply points. 
    
    This model keeps track of them.
    """
    giver = models.ForeignKey("SupplyPoint", related_name="giver", null=True, blank=True)
    giver_unknown = models.CharField(max_length=200, blank=True)
    receiver = models.ForeignKey("SupplyPoint", related_name="receiver")
    product = models.ForeignKey(Product)
    amount = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=StockTransferStatus.STATUS_CHOICES)
    initiated_on = models.DateTimeField(null=True, blank=True)
    closed_on = models.DateTimeField(null=True, blank=True)
    
    def sms_format(self):
        return "%s %s" % (self.product.sms_code, self.amount)
    
    def is_pending(self):
        return self.status == StockTransferStatus.INITIATED
    
    def is_closed(self):
        return not self.is_pending()
    
    def cancel(self, date):
        assert(self.is_pending())
        self.status = StockTransferStatus.CANCELED
        self.closed_on = date
        self.save()
    
    def confirm(self, date):
        assert(self.is_pending())
        self.status = StockTransferStatus.CONFIRMED
        self.closed_on = date
        self.save()
        
    @property
    def giver_display(self):
        return self.giver.name if self.giver else self.giver_unknown
    
    @classmethod
    def pending_transfers(cls):
        return cls.objects.filter(status=StockTransferStatus.INITIATED)
    
    @classmethod
    def create_from_transfer_report(cls, stock_report, receiver):
        """
        Creates stock transfers from a transfer report
        """
        transfers = []
        now = datetime.utcnow()
        # cancel any pending transfers, don't want to accidentally confirm them
        # in response to this
        for pending in cls.pending_transfers().filter(receiver=receiver):
            pending.cancel(now)
        
        for product_code, amount in stock_report.product_stock.items():
            transfers.append(StockTransfer.objects.create(giver=stock_report.supply_point,
                                                          receiver=receiver,
                                                          product=stock_report.get_product(product_code),
                                                          status=StockTransferStatus.INITIATED,
                                                          amount=amount,
                                                          initiated_on=now))
        return transfers
            
    @classmethod
    def create_from_receipt_report(cls, stock_report, supplier):
        """
        Creates stock transfers from a receipt report
        """
        # either we use an official supplier code, or store the 
        # "unknown" value as text
        try:
            sp = SupplyPoint.objects.get(code=supplier)
            sp_unknown = ""
        except SupplyPoint.DoesNotExist:
            sp = None
            sp_unknown = supplier
        
        transfers = []
        now = datetime.utcnow()
        for product_code, amount in stock_report.product_stock.items():
            transfers.append(StockTransfer.objects.create(giver=sp,
                                                          giver_unknown=sp_unknown,
                                                          receiver=stock_report.supply_point,
                                                          product=stock_report.get_product(product_code),
                                                          status=StockTransferStatus.CONFIRMED,
                                                          amount=amount,
                                                          closed_on=now))
        return transfers
        
class StockRequestStatus(object):
    """Basically a const for our choices"""
    REQUESTED = "requested"
    APPROVED = "approved"
    STOCKED_OUT = "stocked_out"
    PARTIALLY_STOCKED = "partially_stocked"
    RECEIVED = "received"
    CANCELED = "canceled"
    CHOICES = [REQUESTED, APPROVED, STOCKED_OUT, PARTIALLY_STOCKED, RECEIVED, CANCELED] 
    CHOICES_PENDING = [REQUESTED, APPROVED, STOCKED_OUT, PARTIALLY_STOCKED]
    CHOICES_CLOSED = [RECEIVED, CANCELED]
    CHOICES_RESPONSE = [APPROVED, STOCKED_OUT, PARTIALLY_STOCKED]
    STATUS_CHOICES = ((val, val) for val in CHOICES)
    RESPONSE_STATUS_CHOICES = ((val, val) for val in CHOICES_RESPONSE)
    
class StockRequest(models.Model):
    """
    In some deployments, you make a stock request, but it's not filled
    immediately. This object keeps track of those requests. It's sort
    of like a special type of ProductReport with a status flag.
    """
    product = models.ForeignKey(Product)
    supply_point = models.ForeignKey("SupplyPoint")
    status = models.CharField(max_length=20, choices=StockRequestStatus.STATUS_CHOICES)
    # this second field is added for auditing purposes
    # the status can change, but once set - this one will not
    response_status = models.CharField(blank=True, max_length=20, choices=StockRequestStatus.RESPONSE_STATUS_CHOICES)
    is_emergency = models.BooleanField(default=False) 
    
    requested_on = models.DateTimeField()
    responded_on = models.DateTimeField(null=True)
    received_on = models.DateTimeField(null=True)
    
    requested_by = models.ForeignKey(Contact, null=True, related_name="requested_by")
    responded_by = models.ForeignKey(Contact, null=True, related_name="responded_by")
    received_by = models.ForeignKey(Contact, null=True, related_name="received_by")
    
    amount_requested = models.PositiveIntegerField(null=True)
    # this field is actually unnecessary with no ability to 
    # approve partial resupplies in the current system, but is
    # left in the models for possibile use down the road
    amount_approved = models.PositiveIntegerField(null=True) 
    amount_received = models.PositiveIntegerField(null=True)
    
    canceled_for = models.ForeignKey("StockRequest", null=True)
    
    def is_pending(self):
        return self.status in StockRequestStatus.CHOICES_PENDING
    
    def is_closed(self):
        return self.status in StockRequestStatus.CHOICES_CLOSED
    
    def approve(self, by, on, amt):
        return self.respond(StockRequestStatus.APPROVED, by, on, amt)
    
    def mark_partial(self, by, on):
        return self.respond(StockRequestStatus.PARTIALLY_STOCKED, by, on)
    
    def mark_stockout(self, by, on):
        return self.respond(StockRequestStatus.STOCKED_OUT, by, on)
    
    def respond(self, status, by, on, amt=None):
        assert(self.is_pending()) # we should only approve pending requests
        # and only respond with valid response statuses
        assert(status in StockRequestStatus.CHOICES_RESPONSE) 
        self.responded_by = by
        if amt:
            self.amount_approved = amt
        self.responded_on = on
        self.status = status
        self.response_status = status
        self.save()
        
    def receive(self, by, amt, on):
        assert(self.is_pending()) # we should only receive pending requests
        self.received_by = by
        self.amount_received = amt
        self.received_on = on
        self.status = StockRequestStatus.RECEIVED
        self.save()
        
    def cancel(self, canceled_for):
        """
        Cancel a supply request, in lieu of a newer one
        """
        assert(self.is_pending()) # we should only cancel pending requests
        self.status = StockRequestStatus.CANCELED
        self.canceled_for = canceled_for
        self.amount_received = 0 # if you cancel it, you didn't get it
        self.save()
    
    def sms_format(self):
        assert(self.status != StockRequestStatus.CANCELED)
        if self.status == StockRequestStatus.REQUESTED:
            return "%s %s" % (self.product.sms_code, self.amount_requested)
        elif self.status == StockRequestStatus.APPROVED:
            return "%s %s" % (self.product.sms_code, self.amount_approved)
        elif self.status == StockRequestStatus.RECEIVED:
            return "%s %s" % (self.product.sms_code, self.amount_received)
        elif self.status in [StockRequestStatus.PARTIALLY_STOCKED, StockRequestStatus.STOCKED_OUT]:
            return self.product.sms_code # no valid amount information
        raise Exception("bad call to sms format, unexpected status: %s" % self.status)
    
    @classmethod
    def pending_requests(cls):
        return cls.objects.filter(status__in=StockRequestStatus.CHOICES_PENDING)
    
    @classmethod
    def create_from_report(cls, stock_report, contact):
        """
        From a stock report helper object, create any pending stock requests.
        """
        requests = []
        now = datetime.utcnow()
        for product_code, stock in stock_report.product_stock.items():
            product = stock_report.get_product(product_code)
            
            current_stock = ProductStock.objects.get(supply_point=stock_report.supply_point, 
                                                     product=product)
            if current_stock.maximum_level > stock:
                # confusingly, we don't flag emergencies unless it is an 
                # emergency level AND an emergency order. this logic
                # is probably not ideal
                is_emergency = stock_report.report_type == Reports.EMERGENCY_SOH and \
                               current_stock.is_below_emergency_level()
                req = StockRequest.objects.create(product=product, 
                                                  supply_point=stock_report.supply_point,
                                                  status=StockRequestStatus.REQUESTED,
                                                  requested_by=contact,
                                                  amount_requested=current_stock.maximum_level - stock,
                                                  requested_on=now, 
                                                  is_emergency=is_emergency)
                requests.append(req)
                pending_requests = StockRequest.pending_requests().filter(supply_point=stock_report.supply_point, 
                                                                          product=product).exclude(pk=req.pk)
                
                # close/delete existing pending stock requests. 
                # The latest one trumps them.
                assert(pending_requests.count() <= 1) # we should never have more than one pending request
                for pending in pending_requests:
                    pending.cancel(req)
                
        return requests
    
    @classmethod
    def close_pending_from_receipt_report(cls, stock_report, contact):
        """
        From a stock report helper object, close any pending stock requests.
        """
        requests = []
        pending_reqs = StockRequest.pending_requests().filter\
            (supply_point=stock_report.supply_point,
             product__sms_code__in=stock_report.product_stock.keys())
        now = datetime.utcnow()
        for req in pending_reqs:
            req.receive(contact, 
                        stock_report.product_stock[req.product.sms_code],
                        now)
            requests.append(req)
        return requests
    
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
    supply_point = models.ForeignKey('SupplyPoint')
    report_type = models.ForeignKey(ProductReportType)
    quantity = models.IntegerField()
    report_date = models.DateTimeField(default=datetime.utcnow)
    # message should only be null if the stock report was provided over the web
    message = models.ForeignKey(Message, blank=True, null=True)

    class Meta:
        verbose_name = "Product Report"
        ordering = ('-report_date',)

    def __unicode__(self):
        return "%s | %s | %s" % (self.supply_point.name, self.product.name, self.report_type.name)

class StockTransaction(models.Model):
    """
     StockTransactions exist to track atomic changes to the ProductStock per facility
     This may look deceptively like the ProductReport. The utility of having a separate
     model is that some ProductReports may be duplicates, invalid, or false reports
     from the field, so how we decide to map reports to transactions may vary 
    """
    product = models.ForeignKey(Product)
    supply_point = models.ForeignKey('SupplyPoint')
    quantity = models.IntegerField()
    # we need some sort of 'balance' field, so that we can get a snapshot
    # of balances over time. we add both beginning and ending balance since
    # the outcome of a transaction might vary, depending on whether balances
    # can be negative or not
    beginning_balance = models.IntegerField()
    ending_balance = models.IntegerField()
    date = models.DateTimeField(default=datetime.utcnow)
    product_report = models.ForeignKey(ProductReport, null=True)
    
    class Meta:
        verbose_name = "Stock Transaction"
        ordering = ('-date',)

    def __unicode__(self):
        return "%s - %s (%s)" % (self.supply_point.name, self.product.name, self.quantity)
    
    @classmethod
    def from_product_report(cls, pr, beginning_balance):
        # no need to generate transaction if it's just a report of 0 receipts
        if pr.report_type.code == RECEIPT_REPORT_TYPE and \
          pr.quantity == 0:
            return None
        # also no need to generate transaction if it's a soh which is the same as before
        if pr.report_type.code == Reports.SOH and \
          beginning_balance == pr.quantity:
            return None
        st = cls(product_report=pr, supply_point=pr.supply_point, 
                 product=pr.product)

        
        st.beginning_balance = beginning_balance
        if pr.report_type.code == Reports.SOH or pr.report_type.code == Reports.EMERGENCY_SOH:
            st.ending_balance = pr.quantity
            st.quantity = st.ending_balance - st.beginning_balance
        elif pr.report_type.code == Reports.REC:
            st.ending_balance = st.beginning_balance
            st.quantity = pr.quantity
        elif pr.report_type.code == Reports.GIVE:
            st.ending_balance = st.beginning_balance
            st.quantity = -pr.quantity
        else:
            err_msg = "UNDEFINED BEHAVIOUR FOR UNKNOWN REPORT TYPE %s" % pr.report_type.code
            logging.error(err_msg)
            raise ValueError(err_msg)
        return st

class RequisitionReport(models.Model):
    supply_point = models.ForeignKey("SupplyPoint")
    submitted = models.BooleanField()
    report_date = models.DateTimeField(default=datetime.utcnow)
    message = models.ForeignKey(Message)

    class Meta:
        ordering = ('-report_date',)

class NagRecord(models.Model):
    supply_point = models.ForeignKey("SupplyPoint")
    report_date = models.DateTimeField(default=datetime.utcnow)
    warning = models.IntegerField(default=1)

    class Meta:
        ordering = ('-report_date',)
    
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

class SupplyPointType(models.Model):
    """
    e.g. medical stores, district hospitals, clinics, community health centers, hsa's
    """
    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True, primary_key=True)

    def __unicode__(self):
        return self.name

class SupplyPoint(models.Model):
    """
    Somewhere that maintains and distributes products. 
    e.g. health centers, hsa's, or regional warehouses.
    """
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    type = models.ForeignKey(SupplyPointType)
    created_at = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=100, unique=True)
    last_reported = models.DateTimeField(default=None, blank=True, null=True)
    location = models.ForeignKey(Location)
    # i know in practice facilities are supplied by a variety of sources
    # but this relationship will only be used to enforce the idealized ordering/
    # supply relationsihp, so having a single ForeignKey mapping is sufficient
    supplied_by = models.ForeignKey('SupplyPoint', blank=True, null=True)

    def __unicode__(self):
        return self.name

    @property
    def label(self):
        return unicode(self)
    
    @property
    def is_active(self):
        return self.active
    
    def deprecate(self, new_code=None):
        """
        Deprecates this supply point, by changing the id and location id,
        and deactivating it.
        """
        if new_code is None:
            new_code = "deprecated-%s-%s" % (self.code, uuid.uuid4()) 
        self.code = new_code
        self.active=False
        self.save()
        self.location.deprecate(new_code=new_code)
        
    def update_stock(self, product, quantity):
        try:
            productstock = ProductStock.objects.get(supply_point=self,
                                                    product=product)
        except ProductStock.DoesNotExist:
            productstock = ProductStock(is_active=settings.LOGISTICS_DEFAULT_PRODUCT_ACTIVATION_STATUS, 
                                        supply_point=self, product=product)
        productstock.quantity = quantity
        productstock.save()
        return productstock

    def stock(self, product):
        try:
            productstock = ProductStock.objects.get(supply_point=self,
                                                    product=product)
        except ProductStock.DoesNotExist:
            return 0
        if productstock.quantity == None:
            return 0
        return productstock.quantity

    def record_consumption_by_code(self, product_code, rate):
        ps = ProductStock.objects.get(product__sms_code=product_code, supply_point=self)
        ps.monthly_consumption = rate
        ps.save()

    def stockout_count(self, product=None, producttype=None):
        return stockout_count(facilities=[self], 
                              product=product, 
                              producttype=producttype)

    def emergency_stock_count(self, product=None, producttype=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        return emergency_stock_count(facilities=[self], 
                                     product=product, 
                                     producttype=producttype)

    def low_stock_count(self, product=None, producttype=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        return low_stock_count(facilities=[self], 
                               product=product, 
                               producttype=producttype)

    def good_supply_count(self, product=None, producttype=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        return good_supply_count(facilities=[self], 
                                 product=product, 
                                 producttype=producttype)

    def overstocked_count(self, product=None, producttype=None):
        return overstocked_count(facilities=[self], 
                                 product=product, 
                                 producttype=producttype)

    def consumption(self, product=None, producttype=None):
        return consumption(facilities=[self], 
                           product=product, 
                           producttype=producttype)

    def report(self, product, report_type, quantity, message=None):
        npr = ProductReport(product=product, report_type=report_type, 
                            quantity=quantity, message=message, supply_point=self)
        npr.save()
        return npr

    def report_stock(self, product, quantity, message=None):
        report_type = ProductReportType.objects.get(code=STOCK_ON_HAND_REPORT_TYPE)
        return self.report(product, report_type, quantity)

    def reporters(self):
        reporters = Contact.objects.filter(supply_point=self)
        reporters = reporters.filter(role__responsibilities__code=STOCK_ON_HAND_RESPONSIBILITY).distinct()
        return reporters

    def reportees(self):
        reporters = Contact.objects.filter(supply_point=self)
        reporters = reporters.filter(role__responsibilities__code=REPORTEE_RESPONSIBILITY).distinct()
        return reporters

    def children(self):
        """
        For all intents and purses, at this time, the 'children' of a facility wrt site navigation
        are the same as the 'children' with respect to stock supply
        """
        return SupplyPoint.objects.filter(supplied_by=self).order_by('name')

    def report_to_supervisor(self, report, kwargs, exclude=None):
        reportees = self.reportees()
        if exclude:
            reportees = reportees.exclude(pk__in=[e.pk for e in exclude])
        for reportee in reportees:
            kwargs['admin_name'] = reportee.name
            reportee.message(report % kwargs)

    def supplies_product(self, product):
        try:
            ps = ProductStock.objects.get(supply_point=self, product=product)
        except ProductStock.DoesNotExist:
            return False
        return ps.is_active

    def activate_product(self, product):
        ps, created = ProductStock.objects.get_or_create(supply_point=self, product=product)
        if not ps.is_active:
            ps.is_active = True
            ps.save()

    def deactivate_product(self, product):
        ps, created = ProductStock.objects.get_or_create(supply_point=self, product=product)
        if ps.is_active:
            ps.is_active = False
            ps.save()

    def notify_suppliees_of_stockouts_resolved(self, stockouts_resolved, exclude=None):
        """ stockouts_resolved is a dictionary of code to product """
        to_notify = SupplyPoint.objects.filter(supplied_by=self).distinct()
        for fac in to_notify:
            reporters = fac.reporters()
            if exclude:
                reporters = reporters.exclude(pk__in=[e.pk for e in exclude])
            for reporter in reporters:
                send_message(reporter.default_connection,
                            "Dear %(name)s, %(supply_point)s has resolved the following stockouts: %(products)s " %
                             {'name':reporter.name,
                             'products':", ".join(stockouts_resolved),
                             'supply_point':self.name})

class Facility(SupplyPoint):
    """A facility is a type of supply point"""
    # it currently has no unique functionality, and will probably be deprecated
    # and removed eventually unless it needs any.
    pass 

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
            raise UnknownFacilityCodeError("Unknown Facility.")
        self.supply_point = sdp
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
                             "Please contact your DHIO for assistance.")
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
        return

    def save(self):
        stockouts_resolved = []
        for stock_code in self.product_stock:
            try:
                original_quantity = ProductStock.objects.get(supply_point=self.supply_point, product__sms_code=stock_code).quantity
            except ProductStock.DoesNotExist:
                original_quantity = 0
            new_quantity = self.product_stock[stock_code]
            self._record_product_report(self.get_product(stock_code), new_quantity, self.report_type)
            # in the case of transfers out this logic is broken
            # for now that's ok, since malawi doesn't do anything with this 
            if original_quantity == 0 and new_quantity > 0:
                stockouts_resolved.append(stock_code)
        if stockouts_resolved:
            # use signals framework to manage custom notifications
            reporter = self.message.contact if self.message else None
            stockout_resolved.send(sender="product_report", supply_point=self.supply_point, 
                                   products=[self.get_product(code) for code in stockouts_resolved], 
                                   resolved_by=reporter)
            
        for stock_code in self.consumption:
            self.supply_point.record_consumption_by_code(stock_code, 
                                                         self.consumption[stock_code])
        for stock_code in self.product_received:
            self._record_product_report(self.get_product(stock_code), 
                                        self.product_received[stock_code], 
                                        RECEIPT_REPORT_TYPE)

    def add_product_consumption(self, product, consumption):
        if isinstance(consumption, basestring) and consumption.isdigit():
            consumption = int(consumption)
        if not isinstance(consumption, int):
            raise TypeError("Consumption must be reported in integers")
        self.consumption[product.sms_code] = consumption
    
    def get_product(self, product_code):
        """
        Gets a product by code, or raises an UnknownCommodityCodeError 
        if the product can't be found.
        """
        try:
            return Product.objects.get(sms_code__icontains=product_code)
        except (Product.DoesNotExist, Product.MultipleObjectsReturned):
            raise UnknownCommodityCodeError(product_code)
    
    def add_product_stock(self, product_code, stock, save=False, consumption=None):
        if isinstance(stock, basestring) and stock.isdigit():
            stock = int(stock)
        if not isinstance(stock, int):
            raise TypeError("Stock must be reported in integers")
        product = self.get_product(product_code)
        if save:
            self._record_product_report(product, stock, self.report_type)
        self.product_stock[product_code] = stock
        if consumption is not None:
            self.consumption[product_code] = consumption
        if stock == 0:
            self.has_stockout = True

    def _record_product_report(self, product, quantity, report_type):
        report_type = ProductReportType.objects.get(code=report_type)
        self.supply_point.report(product=product, report_type=report_type,
                                 quantity=quantity, message=self.message)

    def _record_product_stock(self, product_code, quantity):
        self._record_product_report(product_code, quantity, STOCK_ON_HAND_REPORT_TYPE)

    def _record_product_receipt(self, product, quantity):
        self._record_product_report(product, quantity, RECEIPT_REPORT_TYPE)

    def add_product_receipt(self, product_code, quantity, save=False):
        if isinstance(quantity, basestring) and quantity.isdigit():
            quantity = int(quantity)
        if not isinstance(quantity, int):
            raise TypeError("stock must be reported in integers")
        product = self.get_product(product_code)
        self.product_received[product_code] = quantity
        if save:
            self._record_product_receipt(product, quantity)

    def reported_products(self):
        return set([p for p in self.product_stock])

    def received_products(self):
        return set([p for p in self.product_received])

    def all(self):
        return ", ".join('%s %s' % (key, val) for key, val in self.product_stock.items())
        
    def received(self):
        return ", ".join('%s %s' % (key, val) for key, val in self.product_received.items())
        
    def stockouts(self):
        # slightly different syntax than above, since there's no point in 
        # reporting stock levels for stocks which we know are at level '0'
        return " ".join('%s' % (key) for key, val in self.product_stock.items() if val == 0)
        

    def low_supply(self):
        low_supply = ""
        for i in self.product_stock:
            productstock = ProductStock.objects.filter(supply_point=self.supply_point).get(product__sms_code__icontains=i)
            #if productstock.monthly_consumption == 0:
            #    raise ValueError("I'm sorry. I cannot calculate low
            #    supply for %(code)s until I know your monthly consumption.
            #    Please contact your DHIO for assistance." % {'code':i})
            if productstock.monthly_consumption is not None:
                if self.product_stock[i] <= productstock.monthly_consumption*settings.LOGISTICS_REORDER_LEVEL_IN_MONTHS and \
                   self.product_stock[i] != 0:
                    low_supply = "%s %s" % (low_supply, i)
        low_supply = low_supply.strip()
        return low_supply

    def over_supply(self):
        over_supply = ""
        for i in self.product_stock:
            productstock = ProductStock.objects.filter(supply_point=self.supply_point).get(product__sms_code__icontains=i)
            #if productstock.monthly_consumption == 0:
            #    raise ValueError("I'm sorry. I cannot calculate oversupply
            #    for %(code)s until I know your monthly con/sumption.
            #    Please contact your DHIO for assistance." % {'code':i})
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
        date_check = datetime.utcnow() + relativedelta(days=-7)
        reporter = self.message.contact
        missing_products = Product.objects.filter(Q(reported_by=reporter),
                                                  ~Q(productreport__report_date__gt=date_check,
                                                     productreport__supply_point=self.supply_point) )
        for dict in missing_products.values('sms_code'):
            all_products.append(dict['sms_code'])
        return list(set(all_products)-self.reported_products())

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
        raise UnknownLocationCodeError("Invalid COUNTRY defined in settings.py. Please choose one that matches the code of a registered location.")
    except Location.MultipleObjectsReturned:
        raise Location.MultipleObjectsReturned("You must define only one root location (no parent id) per site.")
    except Location.DoesNotExist:
        raise Location.MultipleObjectsReturned("The COUNTRY specified in settings.py does not exist.")

post_save.connect(post_save_product_report, sender=ProductReport)

def _filtered_stock(product, producttype):
    results = ProductStock.objects.filter(is_active=True)
    if product is not None:
        results = results.filter(product__sms_code=product)
    elif producttype is not None:
        results = results.filter(product__type__code=producttype)
    return results

def stockout_count(facilities=None, product=None, producttype=None):
    results = _filtered_stock(product, producttype).filter(supply_point__in=facilities).filter(quantity=0)
    return results.count()

def emergency_stock_count(facilities=None, product=None, producttype=None):
    """ This indicates all stock below reorder levels,
        including all stock below emergency supply levels
    """
    emergency_stock = 0
    stocks = _filtered_stock(product, producttype).filter(supply_point__in=facilities).filter(quantity__gt=0)
    for stock in stocks:
        if stock.is_below_emergency_level():
            emergency_stock = emergency_stock + 1
    return emergency_stock

def low_stock_count(facilities=None, product=None, producttype=None):
    """ This indicates all stock below reorder levels,
        including all stock below emergency supply levels
    """
    low_stock_count = 0
    stocks = _filtered_stock(product, producttype).filter(supply_point__in=facilities).filter(quantity__gt=0)
    for stock in stocks:
        if stock.is_below_low_supply_but_above_emergency_level():
            low_stock_count = low_stock_count + 1
    return low_stock_count

def good_supply_count(facilities=None, product=None, producttype=None):
    """ This indicates all stock below reorder levels,
        including all stock below emergency supply levels
    """
    good_supply_count = 0
    stocks = _filtered_stock(product, producttype).filter(supply_point__in=facilities).filter(quantity__gt=0)
    for stock in stocks:
        if stock.is_in_good_supply():
            good_supply_count = good_supply_count + 1
    return good_supply_count

def overstocked_count(facilities=None, product=None, producttype=None):
    overstock_count = 0
    stocks = _filtered_stock(product, producttype).filter(supply_point__in=facilities).filter(quantity__gt=0)
    for stock in stocks:
        if stock.is_overstocked():
            overstock_count = overstock_count + 1
    return overstock_count

def consumption(facilities=None, product=None, producttype=None):
    stocks = _filtered_stock(product, producttype).filter(supply_point__in=facilities)
    consumption = stocks.exclude(base_monthly_consumption=None).aggregate(consumption=Sum('base_monthly_consumption'))['consumption']
    return consumption
