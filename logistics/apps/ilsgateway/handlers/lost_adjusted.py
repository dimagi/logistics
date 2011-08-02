#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.ilsgateway.models import ServiceDeliveryPoint, Product, ProductReportType, ContactDetail
from logistics.apps.ilsgateway.utils import *
from dateutil.relativedelta import *
from django.db.models import Q
from django.utils.translation import ugettext as _

class LostAdjusted(KeywordHandler):
    """
    """
    keyword = "la|um"
    def help(self):
        self.respond(_("Please send in your adjustments in the format 'la <product> +-<amount> +-<product> +-<amount>...'"))

    def handle(self, text):
        product_list = text.split()
        if len(product_list) > 0 and len(product_list) % 2 != 0:
             self.respond(_("Sorry, invalid format.  The message should be in the format 'la <product> +-<amount> +-<product> +-<amount>..."))
             return
        else:    
            reported_products = []
            sdp = self.msg.contact.contactdetail.service_delivery_point
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
                        self.respond(_("Sorry, invalid format.  The message should be in the format 'la <product> +-<amount> +-<product> +-<amount>..."))
                        return
                report_type = ProductReportType.objects.filter(sms_code='la')[0:1].get()
                try:
                    product = Product.get_product(product_code)      
                except Product.DoesNotExist:
                    self.respond(_("Sorry, invalid product code %(code)s"), code=product_code.upper())
                    return
                reported_products.append(product.sms_code)
                reply_list.append('%s %s' % (product.sms_code, quantity) )
                sdp.report_product_status(product=product,report_type=report_type,quantity=quantity, message=self.msg.logger_msg)
            now = datetime.now()
            all_products = []
            #TODO: this needs to be fixed not to just check the last 7 days
            date_check = datetime.now() + relativedelta(days=-7)
            missing_products = Product.objects.filter(Q(activeproduct__service_delivery_point=sdp,
                                                        servicedeliverypointproductreport__report_type__sms_code = 'la', 
                                                        activeproduct__is_active=True), 
                                                      ~Q(servicedeliverypointproductreport__report_date__gt=date_check) )
            for dict in missing_products.values('sms_code'):
                all_products.append(dict['sms_code'])
            missing_product_list = list(set(all_products)-set(reported_products))
            if missing_product_list:
                kwargs = {'contact_name': self.msg.contact.name,
                          'facility_name': sdp.name,
                          'product_list': ', '.join(missing_product_list),
                          'reply_list': ','.join(reply_list)}
                                
                self.respond(_('Thank you, you reported your losses/adjustments: %(reply_list)s. Still missing %(product_list)s.'), **kwargs)
            else:    
                self.respond(_('Thank you, you reported your losses/adjustments: %(reply_list)s. If incorrect, please resend.'), reply_list=','.join(reply_list))