#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.ilsgateway.models import ServiceDeliveryPointStatus, ServiceDeliveryPointStatusType, ContactDetail, DeliveryGroup
from rapidsms.models import Connection 
from rapidsms.messages import OutgoingMessage
import datetime
from logistics.apps.ilsgateway.utils import *
from django.utils.translation import ugettext as _

class ConfirmRandRSubmitted(KeywordHandler):
    keyword = "submitted|nimetuma"

    def _send_randr_alert_to_facilities(self, sdp):
        reminder_name = "alert_parent_district_sent_randr"
        contact_details_to_remind = ContactDetail.objects.filter(service_delivery_point__in=sdp.child_sdps_submitting(),
                                                                 primary=True)
        for contact_detail in contact_details_to_remind:
            default_connection = contact_detail.default_connection
            if default_connection:
                kwargs = {'sdp': sdp}
                m = get_message(contact_detail, reminder_name, **kwargs)
                logging.debug("Sending alert to all facilities under %s that R&R forms were sent to MSD" % sdp.name)
                m.send()    
    
    def help(self):
        service_delivery_point=self.msg.contact.contactdetail.service_delivery_point
        if service_delivery_point.service_delivery_point_type.name == "DISTRICT":
            self.respond(_("How many R&R forms have you submitted to MSD for group %(group)s? Reply with 'submitted A <number of R&Rs submitted for group A> B <number of R&Rs submitted for group B>...'"))
        elif service_delivery_point.service_delivery_point_type.name == "FACILITY":
            st = ServiceDeliveryPointStatusType.objects.filter(short_name="r_and_r_submitted_facility_to_district")[0:1].get()
            ns = ServiceDeliveryPointStatus(service_delivery_point=service_delivery_point, status_type=st, status_date=datetime.now())
            ns.save()
            kwargs = {'contact_name': self.msg.contact.name,
                      'sdp_name': self.msg.contact.contactdetail.service_delivery_point.name}
            self.respond(_('Thank you %(contact_name)s for submitting your R and R form for %(sdp_name)s'), **kwargs)
            return
            
    def handle(self, text):
        service_delivery_point=self.msg.contact.contactdetail.service_delivery_point
        if service_delivery_point.service_delivery_point_type.name == "DISTRICT":
            st = ServiceDeliveryPointStatusType.objects.filter(short_name="r_and_r_submitted_district_to_msd")[0:1].get()
            ns = ServiceDeliveryPointStatus(service_delivery_point=service_delivery_point, status_type=st, status_date=datetime.now())
            ns.save()
            
            delivery_groups_list = text.split()
            if len(delivery_groups_list) > 0 and len(delivery_groups_list) % 2 != 0:
                 self.respond(_("Sorry, invalid format.  The message should be in the format 'submitted A <quantity  of R&R forms for group A> B <quantity  of R&R forms for group B>...'"))
                 return
            else:    
                sdp = self.msg.contact.contactdetail.service_delivery_point
                while len(delivery_groups_list) >= 2:
                    quantity = delivery_groups_list.pop(0)
                    delivery_group_name = delivery_groups_list.pop(0)
                    if not is_number(quantity):
                        if is_number(delivery_group_name):
                            temp = delivery_group_name
                            delivery_group_name = quantity
                            quantity = temp
                        else:                        
                            self.respond(_("Sorry, invalid format.  The message should be in the format 'submitted A <quantity  of R&R forms for group A> B <quantity  of R&R forms for group B>...'"))
                            return
                                        
                    try:
                        delivery_group = DeliveryGroup.objects.filter(name__iexact=delivery_group_name)[0:1].get()   
                    except DeliveryGroup.DoesNotExist:
                        kwargs = {'delivery_group_name': delivery_group_name.upper()}
                        self.respond(_("Sorry, invalid Delivery Group %(delivery_group_name)s. Please try again"), **kwargs)
                        return
                    if float(quantity) > service_delivery_point.child_sdps().filter(delivery_group__name__iexact=delivery_group_name).count():
                        kwargs = {'quantity': quantity,
                                  'delivery_group_name': delivery_group_name.upper()}
                        self.respond(_("You reported %(quantity)s forms submitted for group %(delivery_group_name)s, which is more than the number of facilities in group %(delivery_group_name)s. Please try again."), **kwargs)
                        return

                    sdp.report_delivery_group_status(delivery_group=delivery_group,quantity=quantity, message=self.msg.logger_msg)
            kwargs = {'contact_name': self.msg.contact.name,
                      'sdp_name': self.msg.contact.contactdetail.service_delivery_point.name}
            self.respond(_('Thank you %(contact_name)s for reporting your R&R form submissions for %(sdp_name)s'), **kwargs)
            self._send_randr_alert_to_facilities(service_delivery_point)
            return
        elif service_delivery_point.service_delivery_point_type.name == "FACILITY":
            st = ServiceDeliveryPointStatusType.objects.filter(short_name="r_and_r_submitted_facility_to_district")[0:1].get()
            ns = ServiceDeliveryPointStatus(service_delivery_point=service_delivery_point, status_type=st, status_date=datetime.now())
            ns.save()
            kwargs = {'contact_name': self.msg.contact.name,
                      'sdp_name': self.msg.contact.contactdetail.service_delivery_point.name}
            self.respond(_('Thank you %(contact_name)s for submitting your R and R form for %(sdp_name)s'), **kwargs)
            return
        else:
            self.respond(_("Sorry, you need to register."))
        
