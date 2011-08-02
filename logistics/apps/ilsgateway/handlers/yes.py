#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.ilsgateway.models import ServiceDeliveryPointStatus, ServiceDeliveryPointStatusType, ProductReportType, Product
import datetime
import re
from django.utils.translation import ugettext_noop as _
        
class Yes(KeywordHandler):
    """
    """

    keyword = "yes|ndio|ndyo"    

    def help(self):
        self.handle(text="")

    def handle(self, text):
        self.respond(_('If you have submitted your R&R, respond \"submitted\".  If you have received your delivery, respond \"delivered\"'))