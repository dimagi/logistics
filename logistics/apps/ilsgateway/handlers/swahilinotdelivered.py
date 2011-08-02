#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.ilsgateway.models import ServiceDeliveryPointStatus, ServiceDeliveryPointStatusType, ProductReportType, Product
import datetime
import re
from django.utils.translation import ugettext_noop as _

class SwahiliNotDelivered(KeywordHandler):
    
    keyword = "sijapokea"

    def help(self):
        self.handle(text="")
        
    def handle(self, text):
        self.respond(_('You have reported that you haven\'t yet received your delivery.'))
        st = ServiceDeliveryPointStatusType.objects.filter(short_name="delivery_not_received_facility")[0:1].get()
        ns = ServiceDeliveryPointStatus(service_delivery_point=self.msg.contact.contactdetail.service_delivery_point, status_type=st, status_date=datetime.datetime.now())
        ns.save()