#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime, timedelta
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.db.models import Q
from django.utils.translation import ugettext as _
from logistics.apps.logistics.util import config
from logistics.apps.logistics.shortcuts import create_stock_report
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.decorators import logistics_contact_required
import logging
from logistics.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes

CHARS_IN_CODE = "2, 4"
NUMERIC_LETTERS = ("lLIoO", "11100")

class StockOnHandHandler(KeywordHandler):
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
                                           self.msg.logger_msg)
        
        if stock_report.errors:
            self.respond(_(config.Messages.SOH_BAD_FORMAT))
            return
    
        else:    
            # todo, check for missing
            missing_products = [] 
            logging.error("TODO: FIX MISSING PRODUCT GENERATION HERE")
            # start_date = datetime.utcnow() + timedelta(days=-7)
            # Product.objects.filter(Q(activeproduct__service_delivery_point=sdp, activeproduct__is_active=True), 
            # ~Q(servicedeliverypointproductreport__report_date__gt=date_check) )
#            for dict in missing_products.values('sms_code'):
#                all_products.append(dict['sms_code'])
#            missing_product_list = list(set(all_products)-set(reported_products))
            
            if missing_products:
                kwargs = {'contact_name': self.msg.contact.name,
                          'facility_name': sp.name,
                          'product_list': ' '.join(missing_products)}
                self.respond(_(config.Messages.SOH_PARTIAL_CONFIRM), **kwargs)
            else:    
                self.respond(_(config.Messages.SOH_CONFIRM), 
                             reply_list=','.join(sorted(stock_report.reported_products())))
            self.respond(_(config.Messages.SOH_ADJUSTMENTS_REMINDER))
            SupplyPointStatus.objects.create(supply_point=sp, 
                                             status_type=SupplyPointStatusTypes.LOST_ADJUSTED_REMINDER_SENT_TO_FACILITY, 
                                             status_date=datetime.utcnow())
            