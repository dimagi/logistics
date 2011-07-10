#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.utils.translation import ugettext as _
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.models import RequisitionReport
from logistics.util import config

class Help(KeywordHandler):
    keyword = "yes|no|y|n"
    
    def help(self):
        return self.handle(self.msg.text)

    def handle(self, text):
        text = text.strip().lower()
        supply_point = self.msg.contact.supply_point
        if text[0] == 'y':
            submitted = True
            response = config.Messages.REQ_SUBMITTED
        else:
            submitted = False
            response = config.Messages.REQ_NOT_SUBMITTED
        r = RequisitionReport(supply_point=supply_point, submitted=submitted, 
                              message=self.msg.logger_msg)
        r.save()
        self.respond(response)
        return True
