#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime

from re import sub
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.utils.translation import ugettext as _
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.messages import OutgoingMessage
from logistics.apps.logistics.models import Product, \
    ProductStock, ProductReportType, ProductStockReport, RECEIPT_REPORT_TYPE
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
        sdp = self.msg.logistics_contact.location
        stock_report = ProductStockReport(sdp, RECEIPT_REPORT_TYPE, self.msg.logger_msg)
        stock_report.parse(text)
        stock_report.save()
        self.respond(_('Thank you, you reported receipts for %(stocks)s.'), stocks=" ".join(stock_report.reported_products()).strip())
