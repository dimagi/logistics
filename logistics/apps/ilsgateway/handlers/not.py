#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.ilsgateway.models import ServiceDeliveryPointStatus, ServiceDeliveryPointStatusType, ProductReportType, Product
import datetime
import re
from django.utils.translation import ugettext_noop as _
        
class Not(KeywordHandler):
    """
    simple "not"
    """

    keyword = "not|no|hapana"    

    def help(self):
        self.respond(_("If you haven't submitted your R&R, respond \"not submitted\". If you haven't received your delivery, respond \"not delivered\""))

    def handle(self, text):
        if re.match("del", text.strip().lower() ):
            self.respond(_('You have reported that you haven\'t yet received your delivery.'))
            st = ServiceDeliveryPointStatusType.objects.filter(short_name="delivery_not_received_facility")[0:1].get()
            ns = ServiceDeliveryPointStatus(service_delivery_point=self.msg.contact.contactdetail.service_delivery_point, status_type=st, status_date=datetime.datetime.now())
            ns.save()
            
        elif re.match("sub", text.strip().lower() ):
            self.respond(_('You have reported that you haven\'t yet sent in your R&R.'))
            st = ServiceDeliveryPointStatusType.objects.filter(short_name="r_and_r_not_submitted_facility_to_district")[0:1].get()
            ns = ServiceDeliveryPointStatus(service_delivery_point=self.msg.contact.contactdetail.service_delivery_point, status_type=st, status_date=datetime.datetime.now())
            ns.save()
        else:
            self.respond(_("If you haven't submitted your R&R, respond \"not submitted\". If you haven't received your delivery, respond \"not delivered\""))
