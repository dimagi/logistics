#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext_noop as _
        
class Stop(KeywordHandler):
    """
    Stop handler for when a user wants to stop receiving reminders
    """

    keyword = "stop|acha|hapo"    

    def help(self):
        self.respond(_("You have requested to stop reminders to this number.  Send 'help' to this number for instructions on how to reactivate."))
        cd = self.msg.contact.contactdetail
        cd.primary = False
        cd.save()       
    def handle(self, text):
        self.help()