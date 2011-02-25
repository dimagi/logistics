#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext_noop as _
from logistics.apps.logistics.models import Product, REGISTER_MESSAGE

class Stop(KeywordHandler):
    """
    Stop handler for when a user wants to stop receiving reminders
    """

    keyword = "code|codes"
    
    def help(self):
        codes = [c.sms_code for c in Product.objects.all().order_by('sms_code')]
        self.respond("Available commodity codes: %(codes)s", codes=", ".join(codes))

    def handle(self, text):
        self.help()
