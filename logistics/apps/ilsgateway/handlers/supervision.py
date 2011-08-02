#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext_noop as _
import re
from logistics.apps.ilsgateway.models import ServiceDeliveryPointStatus, ServiceDeliveryPointStatusType
import datetime
        
class Supervision(KeywordHandler):
    """
    Supervision handler for responses to supervision inquiries
    """

    keyword = "supervision|usimamizi"    

    def help(self):        
        self.respond(_("Supervision reminders will come monthly, and you can respond 'supervision yes' if you have received supervision or 'supervision no' if you have not"))
    def handle(self, text):
        sub_command = text.strip().lower()
        if re.match("hap", sub_command) or re.match("no", sub_command):
            self.respond(_('You have reported that you have not yet received supervision this month.'))
            st = ServiceDeliveryPointStatusType.objects.filter(short_name="supervision_not_received_facility")[0:1].get()
            print st
            ns = ServiceDeliveryPointStatus(service_delivery_point=self.msg.contact.contactdetail.service_delivery_point, status_type=st, status_date=datetime.datetime.now())
            ns.save()            
        elif re.match("ndi", sub_command) or re.match("yes", sub_command):
            self.respond(_('Thank you for reporting that you have received supervision this month.'))
            st = ServiceDeliveryPointStatusType.objects.filter(short_name="supervision_received_facility")[0:1].get()
            print st
            ns = ServiceDeliveryPointStatus(service_delivery_point=self.msg.contact.contactdetail.service_delivery_point, status_type=st, status_date=datetime.datetime.now())
            ns.save()
        else:
            self.help()
