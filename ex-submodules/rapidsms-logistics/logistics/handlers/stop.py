#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext_noop as _
from logistics.util import config

class Stop(KeywordHandler):
    """
    Stop handler for when a user wants to stop receiving reminders
    """

    keyword = "stop"
    
    def help(self):
        if self.msg.contact is None:
            self.respond(config.Messages.REGISTER_MESSAGE)
            return
        self.respond(_("You have requested to stop reminders to this number.  Send 'help' to this number for instructions on how to reactivate."))
        self.msg.logistics_contact.needs_reminders = False
        self.msg.logistics_contact.save()

    def handle(self, text):
        self.help()
