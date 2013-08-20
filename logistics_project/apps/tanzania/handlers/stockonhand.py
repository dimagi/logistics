#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime, timedelta
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.contrib.handlers.handlers.tagging import TaggingHandler
from django.utils.translation import ugettext_noop as _
from logistics.util import config
from logistics.shortcuts import create_stock_report
from logistics.const import Reports
from logistics.decorators import logistics_contact_required
import logging
from logistics_project.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues
from logistics.models import ProductStock, Product

CHARS_IN_CODE = "2, 4"
NUMERIC_LETTERS = ("lLIoO", "11100")

class StockOnHandHandler(KeywordHandler,TaggingHandler):
    """
    """
    keyword = "soh|hmk"
    
    def help(self):
        self.respond(_(config.Messages.SOH_HELP_MESSAGE))

    @logistics_contact_required()
    def handle(self, text):
        contact = self.msg.logistics_contact
        sp = self.msg.logistics_contact.supply_point
        stock_report = create_stock_report(Reports.SOH,  
                                           sp,
                                           text, 
                                           self.msg.logger_msg,
                                           self.msg.timestamp)
        
        if stock_report.errors:
            self.respond_error(_(config.Messages.SOH_BAD_FORMAT))
            return
    
        else:    
            expected_products = set(contact.commodities.all())
            
            # define missing as products not seen in the last 7 days
            # the exclusion prevents newly added products from counting as "seen"
            start_date = datetime.utcnow() + timedelta(days=-7)
            seen_products = set(Product.objects.get(pk=product_id) for product_id in \
                                ProductStock.objects.filter\
                                    (supply_point=sp, last_modified__gte=start_date)\
                                    .exclude(quantity=None)\
                                    .values_list("product", flat=True))
            
            # if missing products tell them they still need to report, otherwise send confirmation 
            missing_products = expected_products - seen_products
            if missing_products:
                kwargs = {'contact_name': self.msg.contact.name,
                          'facility_name': sp.name,
                          'product_list': ' '.join(sorted([p.sms_code for p in missing_products]))}
                self.respond(_(config.Messages.SOH_PARTIAL_CONFIRM), **kwargs)
            else:    
                self.respond(_(config.Messages.SOH_CONFIRM), 
                             reply_list=','.join(sorted(stock_report.reported_products())))

            SupplyPointStatus.objects.create(supply_point=sp,
                                             status_type=SupplyPointStatusTypes.SOH_FACILITY,
                                             status_value=SupplyPointStatusValues.SUBMITTED,
                                             status_date=self.msg.timestamp)
            # this is an artifact of the response generating the l&a reminder
            SupplyPointStatus.objects.create(supply_point=sp,
                                             status_type=SupplyPointStatusTypes.LOSS_ADJUSTMENT_FACILITY,
                                             status_value=SupplyPointStatusValues.REMINDER_SENT,
                                             status_date=self.msg.timestamp)
            
