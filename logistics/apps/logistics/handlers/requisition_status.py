#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.utils.translation import ugettext as _
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.logistics.models import RequisitionReport

YES_RESPONSE = "Thank you for confirming you have submitted your requisition this month."
NO_RESPONSE = "Please submit your requisition form as soon as possible."

class Help(KeywordHandler):
    keyword = "yes|no|y|n"
    
    def help(self):
        return self.handle(self.msg.text)

    def handle(self, text):
        text = text.strip().lower()
        facility = self.msg.contact.facility
        if text[0] == 'y':
            submitted = True
            response = YES_RESPONSE
        else:
            submitted = False
            response = NO_RESPONSE
        r = RequisitionReport(facility=facility, submitted=submitted, 
                              message=self.msg.logger_msg)
        r.save()
        self.respond(response)
        return True
