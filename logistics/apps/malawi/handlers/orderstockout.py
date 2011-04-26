#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime
from logistics.apps.logistics.models import StockRequest
from logistics.apps.malawi.const import Messages
from logistics.apps.malawi.handlers.abstract.orderresponse import OrderResponseBaseHandler

class OrderStockoutHandler(OrderResponseBaseHandler):
    """
    When a supply has been ordered, it is confirmed "ready" by the person
    providing supplies with this handler.
    """

    keyword = "so|os"

    def help(self):
        self.respond(Messages.STOCKOUT_HELP)
        
    def handle(self, text):
        if self.handle_preconditions(text):
            return
        
        now = datetime.utcnow()
        
        # Currently we just mark these stock requests stocked out.
        pending_reqs = StockRequest.pending_requests().filter(supply_point=self.hsa.supply_point)
        for req in pending_reqs:
            req.mark_stockout(self.msg.logistics_contact, now)
        
        products = ", ".join(req.sms_format() for req in pending_reqs)
        self.respond(Messages.STOCKOUT_RESPONSE, reporter=self.msg.logistics_contact.name,
                     products=products)
        self.hsa.message(Messages.STOCKOUT_NOTICE, hsa=self.hsa.name)
        # TODO: district notifications 
    
                