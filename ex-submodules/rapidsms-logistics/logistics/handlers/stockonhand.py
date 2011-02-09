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
from logistics.apps.logistics.models import ServiceDeliveryPoint, Product, \
    ProductStock, ProductReportType, ProductStockReport

class StockOnHandHandler(KeywordHandler):
    """
    Allows SMS reporters to send in "soh jd 10 mc 30" to report 10 jadelle, 30 male condoms
    """

    keyword = "soh"
    
    def help(self):
        self.respond(_("Please send in your stock on hand information in the format 'soh <product> <amount> <product> <amount>...'"))

    def handle(self, text):
        if not hasattr(self.msg,'logistics_contact'):
            self.respond(_("You must REGISTER before you can submit a stock report." +
                           "Please text 'register <NAME> <MSD_CODE>'."))
            return
        sdp = self.msg.logistics_contact.service_delivery_point
        stock_report = ProductStockReport(sdp, self.msg.logger_msg)
        stock_report.parse(text)
        all_products = []
        date_check = datetime.now() + relativedelta(days=-7)

        # check for products missing
        missing_products = Product.objects.filter(Q(productstock__service_delivery_point=sdp, productstock__is_active=True),
                                                  ~Q(productreport__report_date__gt=date_check) )
        for dict in missing_products.values('sms_code'):
            all_products.append(dict['sms_code'])
        missing_product_list = list(set(all_products)-stock_report.reported_products())
        if missing_product_list:
            kwargs = {'contact_name': self.msg.contact.name,
                      'facility_name': sdp.name,
                      'product_list': ', '.join(missing_product_list)}
            self.respond(_('Thank you %(contact_name)s for reporting your stock on hand for %(facility_name)s.  Still missing %(product_list)s.'), **kwargs)
            return
        if stock_report.has_stockout:
            self.respond(_('The following items are stocked out: %(stocks)s. Please place an order now.'), stocks=stock_report.stockouts())
            return
        low_supply = stock_report.low_supply()
        if low_supply:
            self.respond(_('The following items are in low supply: %(stocks)s. Please place an order now.'), stocks=low_supply)
            return
        self.respond(_('Thank you, you reported you have %(stocks)s. If incorrect, please resend.'), stocks=stock_report.all())

        # notify the supervisor
        sdp.supervisor_report(stock_report)

