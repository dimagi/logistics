#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime
from logistics.apps.logistics.models import StockRequest
from logistics.apps.malawi.const import Messages
from logistics.apps.malawi.handlers.abstract.orderresponse import OrderResponseBaseHandler

class OrderStockoutHandler(OrderResponseBaseHandler):
    """
    When a supply has been ordered, it is confirmed "partial"ly by the person
    providing supplies with this handler.
    """

    keyword = "partial|part"

    def help(self):
        self.respond(Messages.PARTIAL_FILL_HELP)
        
    def handle_custom(self, text):
        
        now = datetime.utcnow()
        
        # Currently we just mark these stock requests partially available.
        # Receipts will clear out the rest
        pending_reqs = StockRequest.pending_requests().filter(supply_point=self.hsa.supply_point)
        for req in pending_reqs:
            req.mark_partial(self.msg.logistics_contact, now)
        
        products = ", ".join(req.sms_format() for req in pending_reqs)
        self.respond(Messages.PARTIAL_FILL_RESPONSE, hsa=self.hsa.name,
                     products=products)
        self.hsa.message(Messages.PARTIAL_FILL_NOTICE, hsa=self.hsa.name)        
    
                