#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.logistics.models import ProductReportsHelper , StockTransfer
from logistics.apps.malawi import util
from logistics.apps.malawi.const import Messages, Operations    
from logistics.apps.malawi.roles import user_can_do
from logistics.apps.logistics.const import Reports

class TransferHandler(KeywordHandler):
    """
    HSA --> HSA transfers
    """

    keyword = "give"

    def help(self):
        self.respond(Messages.TRANSFER_HELP_MESSAGE)
        
    def handle(self, text):
        if not hasattr(self.msg,'logistics_contact'):
            self.respond(Messages.REGISTRATION_REQUIRED_MESSAGE)
        elif not user_can_do(self.msg.logistics_contact, Operations.MAKE_TRANSFER):
            self.respond(Messages.UNSUPPORTED_OPERATION)
        else:
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
                    # todo
                    self.respond("FAIL")
                else:
                    transfers = StockTransfer.create_from_transfer_report(stock_report, hsa.supply_point)
                    self.respond(Messages.TRANSFER_RESPONSE, 
                                 giver=self.msg.logistics_contact.name,
                                 receiver=hsa.name,
                                 products=stock_report.all())
                    hsa.message(Messages.TRANSFER_CONFIRM, 
                                giver=self.msg.logistics_contact.name,
                                products=stock_report.all())
                    