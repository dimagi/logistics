#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime

from re import sub
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.utils.translation import ugettext as _
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.messages import OutgoingMessage
from logistics.apps.logistics.models import ServiceDeliveryPoint, Product, ProductReportType

class StockOnHandHandler(KeywordHandler):
    """
    Allows SMS reporters to send in "soh jd 10 mc 30" to report 10 jadelle, 30 male condoms
    """

    keyword = "soh"
    
    def help(self):
        self.respond(_("Please send in your stock on hand information in the format 'soh <product> <amount> <product> <amount>...'"))

    def handle(self, text):
        product_list = text.split()
        if len(product_list) > 0 and len(product_list) % 2 != 0:
             self.respond(_("Sorry, invalid format.  The message should be in the format 'soh <product> <amount> <product> <amount>...'"))
             return
        else:
            reported_products = []
            sdp = self.msg.logistics_contact.service_delivery_point
            reply_list = []
            while len(product_list) >= 2:
                product_code = product_list.pop(0)
                quantity = product_list.pop(0)
                report_type = ProductReportType.objects.get(slug='soh')
                try:
                    product = Product.objects.get(sms_code__contains=product_code)
                except Product.DoesNotExist:
                    self.respond(_("Sorry, invalid product code %(code)s"), code=product_code.upper())
                    return
                reported_products.append(product.sms_code)
                reply_list.append('%s %s' % (product.sms_code, quantity) )
                sdp.report(product=product,report_type=report_type,quantity=quantity, message=self.msg.logger_msg)
            all_products = []
            date_check = datetime.now() + relativedelta(days=-7)
            missing_products = Product.objects.filter(Q(productstock__service_delivery_point=sdp, productstock__is_active=True),
                                                      ~Q(productreport__report_date__gt=date_check) )
            for dict in missing_products.values('sms_code'):
                all_products.append(dict['sms_code'])
            missing_product_list = list(set(all_products)-set(reported_products))
            if missing_product_list:
                kwargs = {'contact_name': self.msg.contact.name,
                          'facility_name': sdp.name,
                          'product_list': ', '.join(missing_product_list)}
                self.respond(_('Thank you %(contact_name)s for reporting your stock on hand for %(facility_name)s.  Still missing %(product_list)s.'), **kwargs)
            else:
                self.respond(_('Thank you, you reported you have %(reply_list)s. If incorrect, please resend.'), reply_list=','.join(reply_list))
