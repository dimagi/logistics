#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.utils.translation import ugettext as _
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.logistics.models import Product

HELP_TEXT = "Text 'help stock' for help on the format of stock reports; " + \
            "'help codes' for a list of commodity codes; " + \
            "'help start' or 'help stop' to start and stop reminders."

class Help(KeywordHandler):
    keyword = "help"


    def help(self):
        self.respond(HELP_TEXT)

    def handle(self, text):
        topic = text.strip().lower()
        if topic == 'stock':
            self.respond(_("Please send your receipts in the format ' <Commodity code> <stock on hand > . <quantity received>'"))
        elif topic == 'stop':
            self.respond(_("Text 'stop' to stop receiving text message reminders."))
        elif topic == 'start':
            self.respond(_("Text 'start' to get text message reminders every week to submit your stock reports."))
        elif 'code' in topic:
            codes = [c.sms_code for c in Product.objects.all().order_by('sms_code')]
            self.respond("Available commodity codes: %(codes)s", codes=", ".join(codes))
        else:
            try:
                p = Product.objects.get(sms_code=topic)
                msg = "%s is the commodity code for %s" % (topic, p.name)
                if p.units:
                    msg = msg + " (%s)" % p.units
                if p.description:
                    if p.description not in p.name:
                        msg = msg + " %s" % p.description
                self.respond(msg)
            except Product.DoesNotExist:
                self.respond(HELP_TEXT)
