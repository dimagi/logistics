#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.utils.translation import ugettext as _
from rapidsms.conf import settings
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole, Facility, SupplyPoint, REGISTER_MESSAGE, SupplyPointType,\
    StockRequest
from rapidsms.contrib.locations.models import Location, LocationType
from logistics.apps.malawi import const, util
from logistics.apps.malawi.const import Messages, Operations,\
    hsa_supply_point_type
from logistics.apps.malawi.roles import user_can_do

class OrderReadyHandler(KeywordHandler):
    """
    When a supply has been ordered, it is confirmed "ready" by the person
    providing supplies with this handler.
    """

    keyword = "ready"

    def help(self):
        self.respond(Messages.ORDERREADY_HELP_MESSAGE)
        
    def handle(self, text):
        if not hasattr(self.msg,'logistics_contact'):
            self.respond(Messages.REGISTRATION_REQUIRED_MESSAGE)
        elif not user_can_do(self.msg.logistics_contact, Operations.FILL_ORDER):
            self.respond(Messages.UNSUPPORTED_OPERATION)
        else:
            words = text.split(" ")
            hsa_id = words[0]
            hsa = util.get_hsa(hsa_id)
            if hsa is None:
                self.respond(Messages.UNKNOWN_HSA, hsa_id=hsa_id)
            else:
                pending_reqs = StockRequest.pending_requests().filter(supply_point=hsa.supply_point)
                for req in pending_reqs:
                    req.approve(self.msg.logistics_contact, req.amount_requested)
                
                products = ", ".join(req.sms_format() for req in pending_reqs)
                self.respond(Messages.APPROVAL_RESPONSE, hsa=hsa.name,
                             products=products)
                hsa.message(Messages.APPROVAL_NOTICE, hsa=hsa.name, 
                            products=products)
            
                