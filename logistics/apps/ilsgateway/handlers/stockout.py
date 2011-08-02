#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.ilsgateway.models import ServiceDeliveryPoint, Product, ProductReportType, ContactDetail
from logistics.apps.ilsgateway.utils import *
from dateutil.relativedelta import *
from django.db.models import Q
from django.utils.translation import ugettext as _

class StockOut(KeywordHandler):
    """
    """
    keyword = "stockout|hakuna"
    def help(self):
        self.respond(_("Please send in stockout reports in the form 'so <product>'"))

    def handle(self, text):
        product_code = text.strip().upper()
        try:
            product = Product.get_product(product_code)      
        except Product.DoesNotExist:
            self.respond(_("Sorry, invalid product code %(code)s"), code=product_code)
            return
        sdp = self.msg.contact.contactdetail.service_delivery_point
        report_type = ProductReportType.objects.filter(sms_code='soh')[0:1].get()
        sdp.report_product_status(product=product,report_type=report_type,quantity=0, message=self.msg.logger_msg)
        kwargs = {'contact_name': self.msg.contact.name,
                  'facility_name': sdp.name,
                  'product_name': product.name}
        self.respond(_('Thank you %(contact_name)s for reporting a stockout of %(product_name)s for %(facility_name)s.'), **kwargs)
