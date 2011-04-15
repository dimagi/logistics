#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext_noop as _
from logistics.apps.logistics.models import REGISTER_MESSAGE
from logistics.apps.logistics.models import ProductReport, ProductStock

class Stop(KeywordHandler):
    """
    Stop handler for when a user wants to stop receiving reminders
    """

    keyword = "sta|stat|status"
    
    def help(self):
        self.handle("")

    def handle(self, text):
        if self.msg.contact is None:
            self.respond(REGISTER_MESSAGE)
            return
        reports = ProductReport.objects.filter(message__contact=self.msg.contact)
        if not reports:
            self.respond("You have not submitted any stock reports yet.")
        last_report = reports.order_by("-report_date")[0]
        self.respond(("You sent: %s" % last_report.message.text)[:160])

