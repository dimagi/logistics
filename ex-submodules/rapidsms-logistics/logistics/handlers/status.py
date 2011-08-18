#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.models import ProductReport
from logistics.util import config
from logistics.handlers import logistics_keyword

class Stop(KeywordHandler):
    """
    Stop handler for when a user wants to stop receiving reminders
    """

    keyword = logistics_keyword("sta|stat|status")
    
    def help(self):
        self.handle("")

    def handle(self, text):
        if self.msg.contact is None:
            self.respond(config.Messages.REGISTER_MESSAGE)
            return
        if config.Responsibilities.REPORTEE_RESPONSIBILITY in self.msg.contact.role.responsibilities.values_list('code', flat=True):
            # if a super, show last report from your facility
            reports = ProductReport.objects.filter(facility=self.msg.contact.facility)
            if not reports:
                self.respond("Your facility has not submitted any stock reports yet.")
                return
            resp = "Last Report: '%(report)s' on %(date)s"
        else:
            # else if a reporter, show your last report
            reports = ProductReport.objects.filter(message__contact=self.msg.contact)
            if not reports:
                self.respond("You have not submitted any stock reports yet.")
                return
            resp = "You sent '%(report)s' on %(date)s "
        last_report = reports.order_by("-report_date")[0]
        self.respond(resp % {'report': last_report.message.text, 
                              'date': last_report.report_date.strftime('%h %d')})

