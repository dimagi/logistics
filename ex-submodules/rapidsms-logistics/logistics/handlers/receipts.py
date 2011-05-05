#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.utils.translation import ugettext as _
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.logistics.models import ProductReportsHelper, RECEIPT_REPORT_TYPE,\
    StockRequest, StockTransfer
from logistics.apps.logistics.decorators import logistics_contact_required
from logistics.apps.logistics.util import config

class ReceiptHandler(KeywordHandler):
    """
    Allows SMS reporters to send in "rec jd 10 mc 30" to report 10 jadelle and 30 male condoms received
    """

    keyword = "rec|receipts|received"

    def help(self):
        self.respond(_("Please send in information about your receipts in the format 'rec <product> <amount> <product> <amount>...'"))

    @logistics_contact_required()
    def handle(self, text):
        # at the end of your receipt message you can write:
        # 'from xxx' to indicate the source of the supplies.
        # this is used in the stock transfer workflow
        # TODO: less brittle parsing
        if "from" in text.lower().split():
            splittext = text.lower().split()
            text = " ".join(splittext[:splittext.index("from")])
            supplier = " ".join(splittext[splittext.index("from") + 1:])
        else:
            supplier = None
        
        # parse the report and save as normal receipt
        stock_report = ProductReportsHelper(self.msg.logistics_contact.supply_point, 
                                            RECEIPT_REPORT_TYPE, self.msg.logger_msg)
        stock_report.parse(text)
        stock_report.save()
        
        # Close pending requests. This logic only applies if you are using the 
        # StockRequest workflow, but should not break anything if you are not
        StockRequest.close_pending_from_receipt_report(stock_report, self.msg.logistics_contact)
        
        # fill in transfers, if there were any
        if supplier is not None:
            StockTransfer.create_from_receipt_report(stock_report, supplier)

        self.respond(_(config.Messages.RECEIPT_CONFIRM), products=" ".join(stock_report.reported_products()).strip())
