#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.models import StockTransfer
from logistics.const import Reports
from logistics.util import config
from logistics_project.apps.malawi.util import get_hsa
from logistics.decorators import logistics_contact_and_permission_required
from logistics_project.apps.malawi.shortcuts import send_transfer_responses
from logistics.shortcuts import create_stock_report


class TransferHandler(KeywordHandler):
    """
    HSA --> HSA transfers
    """

    keyword = "give"

    def help(self):
        self.respond(config.Messages.TRANSFER_HELP_MESSAGE)
    
    @logistics_contact_and_permission_required(config.Operations.MAKE_TRANSFER)
    def handle(self, text):
        words = text.split(" ")
        # need at least a keyword and 1 product + amount
        if len(words) < 3: 
            return self.help()
        hsa_id = words[0]
        remainder = " ".join(words[1:])
        hsa = get_hsa(hsa_id)
        if hsa is None:
            self.respond(config.Messages.UNKNOWN_HSA, hsa_id=hsa_id)
        else:
            stock_report = create_stock_report(Reports.GIVE,  
                                               self.msg.logistics_contact.supply_point,
                                               remainder, 
                                               self.msg.logger_msg)
            transfers = StockTransfer.create_from_transfer_report(stock_report, hsa.supply_point)
            send_transfer_responses(self.msg, stock_report, transfers, self.msg.logistics_contact, hsa)