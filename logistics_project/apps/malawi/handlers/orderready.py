#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime
from logistics.models import StockRequest
from logistics.util import config
from logistics_project.apps.malawi.handlers.abstract.orderresponse import OrderResponseBaseHandler

class OrderReadyHandler(OrderResponseBaseHandler):
    """
    When a supply has been ordered, it is confirmed "ready" by the person
    providing supplies with this handler.
    """

    keyword = "ready"

    def help(self):
        self.respond(config.Messages.ORDERREADY_HELP_MESSAGE)
        
    def handle_custom(self, text):
        now = datetime.utcnow()
        pending_reqs = StockRequest.pending_requests().filter(supply_point=self.hsa.supply_point)
        for req in pending_reqs:
            req.approve(self.msg.logistics_contact, now, req.amount_requested)
        
        self.respond(config.Messages.APPROVAL_RESPONSE, hsa=self.hsa.name)
        self.hsa.message(config.Messages.APPROVAL_NOTICE, hsa=self.hsa.name)
    
        # this is really hacky, but set the SoH to non-zero for the reported products
        # so that they show no longer stocked out in things like alerts
        for req in pending_reqs:
            if self.msg.logistics_contact.supply_point.stock(req.product) == 0:
                self.msg.logistics_contact.supply_point.update_stock(req.product, 1)
