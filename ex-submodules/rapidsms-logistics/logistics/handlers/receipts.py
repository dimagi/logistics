#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from django.utils.translation import ugettext as _
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.logistics.models import ProductReportsHelper, RECEIPT_REPORT_TYPE,\
    StockRequest
from logistics.apps.logistics.models import REGISTER_MESSAGE

class ReceiptHandler(KeywordHandler):
    """
    Allows SMS reporters to send in "rec jd 10 mc 30" to report 10 jadelle and 30 male condoms received
    """

    keyword = "rec|receipts|received"

    def help(self):
        self.respond(_("Please send in information about your receipts in the format 'rec <product> <amount> <product> <amount>...'"))

    def handle(self, text):
        if not hasattr(self.msg,'logistics_contact'):
            self.respond(REGISTER_MESSAGE)
            return
        facility = self.msg.logistics_contact.supply_point
        stock_report = ProductReportsHelper(facility, RECEIPT_REPORT_TYPE, self.msg.logger_msg)
        stock_report.parse(text)
        stock_report.save()
        # Close pending requests. This logic only applies if you are using the 
        # StockRequest workflow, but should not break anything if you are not
        pending_reqs = StockRequest.pending_requests().filter\
            (supply_point=self.msg.logistics_contact.supply_point,
             product__sms_code__in=stock_report.product_stock.keys())
        now = datetime.utcnow()
        for req in pending_reqs:
            req.receive(self.msg.logistics_contact, 
                        stock_report.product_stock[req.product.sms_code],
                        now)
                
        self.respond(_('Thank you, you reported receipts for %(stocks)s.'), stocks=" ".join(stock_report.reported_products()).strip())
