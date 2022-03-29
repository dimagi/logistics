#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from __future__ import unicode_literals
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from logistics.util import config

class DeregistrationHandler(KeywordHandler):
    """
    Leave the system with "leave"
    """

    keyword = "leave"

    def help(self):
        self.handle("")
        
    def handle(self, text):
        if not hasattr(self.msg,'logistics_contact'):
            self.respond(config.Messages.LEAVE_NOT_REGISTERED)
        else:
            self.msg.logistics_contact.is_active = False
            self.msg.logistics_contact.save()
            if self.msg.logistics_contact.supply_point and \
               self.msg.logistics_contact.supply_point.type == config.hsa_supply_point_type():
                #self.msg.logistics_contact.supply_point.deprecate()
                self.msg.logistics_contact.supply_point.active = False
                self.msg.logistics_contact.supply_point.save()
                self.msg.logistics_contact.supply_point.location.is_active = False
                self.msg.logistics_contact.supply_point.location.save()

            self.respond(config.Messages.LEAVE_CONFIRM)
