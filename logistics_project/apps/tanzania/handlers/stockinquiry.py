#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.contrib.handlers.handlers.tagging import TaggingHandler
from django.utils.translation import ugettext_noop as _
from logistics.util import config
from logistics.const import Reports
from logistics.decorators import logistics_contact_required
from logistics.models import Product, ProductReportsHelper

class StockInquiryHandler(KeywordHandler,TaggingHandler):
    """
    """
    keyword = "si"
    
    def help(self):
        self.respond(_(config.Messages.STOCK_INQUIRY_HELP_MESSAGE))

    @logistics_contact_required()
    def handle(self, text):
        sp = self.msg.logistics_contact.supply_point
        result = text.split()
        product_code = result[0]
        amt = result[1]
        p = Product.objects.get(product_code=product_code)
        prh = ProductReportsHelper(sp, Reports.SOH)
        prh.add_product_stock(p.sms_code, amt)
        prh.save()
        self.respond(_(config.Messages.STOCK_INQUIRY_CONFIRM),
                     **{"quantity": amt, "product_name": p.name})
