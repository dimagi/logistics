#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext_noop as _
from logistics.apps.logistics.models import REGISTER_MESSAGE
from logistics.apps.logistics.models import ProductReport, ProductStock, \
    REPORTEE_RESPONSIBILITY

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
        if REPORTEE_RESPONSIBILITY in self.msg.contact.role.responsibilities.values_list('code', flat=True):
            # if a super, show last report from your facility
            reports = ProductReport.objects.filter(facility=self.msg.contact.facility)
            if not reports:
                self.respond("Your facility has not submitted any stock reports yet.")
            resp = "Last Report: %s"
        else:
            # else if a reporter, show your last report
            reports = ProductReport.objects.filter(message__contact=self.msg.contact)
            if not reports:
                self.respond("You have not submitted any stock reports yet.")
            resp = "You sent: %s"
        last_report = reports.order_by("-report_date")[0]
        self.respond((resp % last_report.message.text)[:160])

