#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.logistics.models import ProductReportsHelper , StockTransfer
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.util import config
from config import Messages
from config import Operations
from logistics.apps.malawi import util
from logistics.apps.logistics.decorators import logistics_contact_and_permission_required

class TransferHandler(KeywordHandler):
    """
    HSA --> HSA transfers
    """

    keyword = "give"

    def help(self):
        self.respond(Messages.TRANSFER_HELP_MESSAGE)
    
    @logistics_contact_and_permission_required(Operations.MAKE_TRANSFER)
    def handle(self, text):
        words = text.split(" ")
        hsa_id = words[0]
        hsa = util.get_hsa(hsa_id)
        if hsa is None:
            self.respond(Messages.UNKNOWN_HSA, hsa_id=hsa_id)
        else:
            # deduct from the sender, add to the receiver.
            stock_report = ProductReportsHelper(self.msg.logistics_contact.supply_point, 
                                                Reports.GIVE, self.msg.logger_msg)
            stock_report.parse(text)
            stock_report.save()
            if stock_report.errors:
                # TODO: respond better.
                self.respond(Messages.GENERIC_ERROR)
            else:
                transfers = StockTransfer.create_from_transfer_report(stock_report, hsa.supply_point)
                self.respond(Messages.TRANSFER_RESPONSE, 
                             giver=self.msg.logistics_contact.name,
                             receiver=hsa.name,
                             products=stock_report.all())
                hsa.message(Messages.TRANSFER_CONFIRM, 
                            giver=self.msg.logistics_contact.name,
                            products=stock_report.all())
                