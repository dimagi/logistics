    #!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics_project.apps.ilsgateway.models import ServiceDeliveryPointStatus, ServiceDeliveryPointStatusType, ProductReportType, Product, ContactDetail
from datetime import *
from logistics_project.apps.ilsgateway.utils import *
from django.utils.translation import ugettext_noop as _
        
class ConfirmDeliveryReceived(KeywordHandler):
    """
    for reporting delivery confirmation, products and amounts
    """

    keyword = "delivered|dlvd|nimepokea"
    
    def _send_delivery_alert_to_facilities(self, sdp):
        reminder_name = "alert_parent_district_delivery_received_sent_facility"
        contact_details_to_remind = ContactDetail.objects.filter(service_delivery_point__in=sdp.child_sdps_receiving(),
                                                                 primary=True)
        for contact_detail in contact_details_to_remind:
            default_connection = contact_detail.default_connection
            if default_connection:
                kwargs = {'sdp': sdp}
                m = get_message(contact_detail, reminder_name, **kwargs)
                logging.debug("Sending alert to all facilities under %s that they received delivery from from MSD" % sdp.name)
                m.send()

    def help(self):
        service_delivery_point=self.msg.contact.contactdetail.service_delivery_point
        if service_delivery_point.service_delivery_point_type.name == "DISTRICT":
            st = ServiceDeliveryPointStatusType.objects.filter(short_name="delivery_received_district")[0:1].get()
            ns = ServiceDeliveryPointStatus(service_delivery_point=service_delivery_point, status_type=st, status_date=datetime.now())
            ns.save()
            kwargs={'contact_name': self.msg.contact.name,
                    'facility_name': service_delivery_point.name}
            self.respond(_('Thank you %(contact_name)s for reporting your delivery for %(facility_name)s'), **kwargs)
            self._send_delivery_alert_to_facilities(service_delivery_point)
        elif service_delivery_point.service_delivery_point_type.name == "FACILITY":
            st = ServiceDeliveryPointStatusType.objects.filter(short_name="delivery_received_facility")[0:1].get()
            ns = ServiceDeliveryPointStatus(service_delivery_point=service_delivery_point, status_type=st, status_date=datetime.now())
            ns.save()
            self.respond(_("To record a delivery, respond with \"delivered product amount product amount...\""))

    def handle(self, text):
        service_delivery_point=self.msg.contact.contactdetail.service_delivery_point
        if service_delivery_point.service_delivery_point_type.name == "DISTRICT":
            st = ServiceDeliveryPointStatusType.objects.filter(short_name="delivery_received_district")[0:1].get()
            ns = ServiceDeliveryPointStatus(service_delivery_point=service_delivery_point, status_type=st, status_date=datetime.now())
            ns.save()
            kwargs={'contact_name': self.msg.contact.name,
                    'facility_name': service_delivery_point.name}
            self.respond(_('Thank you %(contact_name)s for reporting your delivery for %(facility_name)s'), **kwargs)
            self._send_delivery_alert_to_facilities(service_delivery_point)
        elif service_delivery_point.service_delivery_point_type.name == "FACILITY":
            product_list = text.split()
            if len(product_list) > 0 and len(product_list) % 2 != 0:
                 self.respond(_("Sorry, invalid format.  The message should be in the format 'delivered product amount product amount'"))
                 return
            else:
                reply_list = []
                while len(product_list) >= 2:
                    product_code = product_list.pop(0)
                    quantity = product_list.pop(0)
                    if not is_number(quantity):
                        if is_number(product_code):
                            temp = product_code
                            product_code = quantity
                            quantity = temp
                        else:                        
                            self.respond(_("Sorry, invalid format.  The message should be in the format 'delivered product amount product amount'"))
                            return
                    
                    report_type = ProductReportType.objects.filter(sms_code='dlvd')[0:1].get()
                    try:
                        product = Product.get_product(product_code)      
                    except Product.DoesNotExist:
                        self.respond(_('Sorry, invalid product code %(code)s'), code=product_code)
                        return
                    reply_list.append('%s %s' % (product.sms_code, quantity) )
                    service_delivery_point.report_product_status(product=product,report_type=report_type,quantity=quantity, message=self.msg.logger_msg)
                
                st = ServiceDeliveryPointStatusType.objects.filter(short_name="delivery_quantities_reported")[0:1].get()
                ns = ServiceDeliveryPointStatus(service_delivery_point=service_delivery_point, status_type=st, status_date=datetime.now())
                ns.save()
                self.respond(_('Thank you, you reported a delivery of %(reply_list)s. If incorrect, please resend.'), reply_list=','.join(reply_list))             