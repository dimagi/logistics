#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.contrib.handlers.handlers.tagging import TaggingHandler
from django.utils.translation import ugettext_noop as _
from logistics.util import config
from logistics.decorators import logistics_contact_required
        
class Stop(KeywordHandler,TaggingHandler):
    """
    Stop handler for when a user wants to stop receiving reminders
    """

    keyword = "stop|acha|hapo"    

    def help(self):
        return self.handle("")
        
    @logistics_contact_required()
    def handle(self, text):
        self.msg.contact.is_active = False
        self.msg.contact.save()
        self.respond(_(config.Messages.STOP_CONFIRM))
        
    
