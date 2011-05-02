#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from logistics.apps.malawi import const
from logistics.apps.malawi.const import Messages

class HSADeregistrationHandler(KeywordHandler):
    """
    Allow remote users to set their preferred language, by updating the
    ``language`` field of the Contact associated with their connection.
    """

    keyword = "leave"

    def help(self):
        self.handle("")
        
    def handle(self, text):
        if not hasattr(self.msg,'logistics_contact'):
            self.respond(Messages.LEAVE_NOT_REGISTERED)
        else:
            self.msg.logistics_contact.is_active = False
            self.msg.logistics_contact.save()
            if self.msg.logistics_contact.supply_point and \
               self.msg.logistics_contact.supply_point.type == const.hsa_supply_point_type():
                self.msg.logistics_contact.supply_point.deprecate()
            
            self.respond(Messages.LEAVE_CONFIRM)
        