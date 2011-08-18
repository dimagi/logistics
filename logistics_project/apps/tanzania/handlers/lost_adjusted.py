#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext as _
from logistics.util import config
from logistics.decorators import logistics_contact_required
from logistics.shortcuts import create_stock_report
from logistics.const import Reports
import logging

class LostAdjusted(KeywordHandler):
    """
    Losses and adjustments
    """
    
    keyword = "la|um"
    
    def help(self):
        self.respond(_(config.Messages.LOSS_ADJUST_HELP))

    @logistics_contact_required()
    def handle(self, text):
        contact = self.msg.logistics_contact
        sp = self.msg.logistics_contact.supply_point
        stock_report = create_stock_report(Reports.LOSS_ADJUST,  
                                           sp,
                                           text, 
                                           self.msg.logger_msg,
                                           timestamp=self.msg.timestamp)
        
        if stock_report.errors:
            self.respond(_(config.Messages.LOSS_ADJUST_BAD_FORMAT))
            return
    
        else:    
            logging.error("TODO: check for full product list here")
#            now = datetime.now()
#            all_products = []
#            #TODO: this needs to be fixed not to just check the last 7 days
#            date_check = datetime.now() + relativedelta(days=-7)
#            missing_products = Product.objects.filter(Q(activeproduct__service_delivery_point=sdp,
#                                                        servicedeliverypointproductreport__report_type__sms_code = 'la', 
#                                                        activeproduct__is_active=True), 
#                                                      ~Q(servicedeliverypointproductreport__report_date__gt=date_check) )
#            for dict in missing_products.values('sms_code'):
#                all_products.append(dict['sms_code'])
#            missing_product_list = list(set(all_products)-set(reported_products))
#            if missing_product_list:
#                kwargs = {'contact_name': self.msg.contact.name,
#                          'facility_name': sdp.name,
#                          'product_list': ', '.join(missing_product_list),
#                          'reply_list': ','.join(reply_list)}
#                                
#                
            
            if False:
                kwargs = {} # fix!
                self.respond(_('Thank you, you reported your losses/adjustments: %(reply_list)s. Still missing %(product_list)s.'), **kwargs)
            else:
                self.respond(_(config.Messages.LOSS_ADJUST_CONFIRM))