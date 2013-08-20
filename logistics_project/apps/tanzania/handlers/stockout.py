#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.contrib.handlers.handlers.tagging import TaggingHandler
from django.utils.translation import ugettext_noop as _
from logistics.util import config
from logistics.models import Product
from logistics.shortcuts import create_stock_report
from logistics.const import Reports
from logistics.decorators import logistics_contact_required

class StockOut(KeywordHandler,TaggingHandler):
    """
    When someone is stocked out they report it here
    """
    
    keyword = "stockout|hakuna"
    
    def help(self):
        self.respond(_(config.Messages.STOCKOUT_HELP))

    @logistics_contact_required()
    def handle(self, text):
        words = set(t.lower() for t in text.split(" "))
        if not words:
            self.add_tag("Error")
            return self.help()
        
        products = [Product.objects.get(sms_code__iexact=code) for code in words \
                    if Product.objects.filter(sms_code__iexact=code).exists()]
        
        if len(products) != len(words):
            bad = words - set([p.sms_code.lower() for p in products])
            self.respond_error(_(config.Messages.INVALID_PRODUCT_CODE), product_code=" ".join(bad))
            return 
        
        # fake a soh report with the stock level set to 0 for all products
        fake_report_text = " ".join(["%s 0" % p.sms_code for p in products])
        stock_report = create_stock_report(Reports.SOH,  
                                           self.msg.logistics_contact.supply_point,
                                           fake_report_text,
                                           self.msg.logger_msg,
                                           self.msg.timestamp)
        
        kwargs = {'contact_name': self.msg.logistics_contact.name,
                  'facility_name': self.msg.logistics_contact.supply_point.name,
                  'product_names': " ".join(sorted(words))}
        self.respond(_(config.Messages.STOCKOUT_CONFIRM), **kwargs)
