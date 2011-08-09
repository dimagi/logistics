#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics_project.apps.ilsgateway.models import ServiceDeliveryPoint, Product, ProductReportType, ContactDetail, ServiceDeliveryPointStatus, ServiceDeliveryPointStatusType
from logistics_project.apps.ilsgateway.utils import *
from dateutil.relativedelta import *
from django.db.models import Q
from django.utils.translation import ugettext as _
from rapidsms.messages import OutgoingMessage
from re import sub

class StockOnHandHandler(KeywordHandler):
    """
    """
    keyword = "si"
    def help(self):
        self.respond(_("Please send in your stock on hand information in the format 'si <MSD product code> <amount>'"))

    def handle(self, text):
        product_code, quantity = text.split()
        product_code = sub('m|M', '', product_code)
        if not product_code and quantity:
             self.respond(_("Sorry, invalid format.  The message should be in the format 'si <MSD product code> <amount>'"))
             return
        else:    
            sdp = self.msg.contact.contactdetail.service_delivery_point
            try:
                product = Product.get_product(product_code)   
            except Product.DoesNotExist:
                self.respond(_("Sorry, invalid product code %(code)s"), code=product_code.upper())
                return
            if not is_number(quantity):
                self.respond(_("Sorry, invalid format.  The message should be in the format 'si <MSD product code> <amount>'"))
                return
            report_type = ProductReportType.objects.filter(sms_code='soh')[0:1].get()
            sdp.report_product_status(product=product,report_type=report_type,quantity=quantity, message=self.msg.logger_msg)
            self.respond(_('Thank you, you reported you have %(quantity)s     %(product_name)s. If incorrect, please resend.'), product_name=product.name, quantity=quantity)        