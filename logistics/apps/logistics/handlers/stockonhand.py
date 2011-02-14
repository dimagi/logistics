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
    ProductStock, ProductReportType, ProductStockReport, STOCK_ON_HAND_REPORT_TYPE

ERR_MSG = _("Please send your stock on hand in the format 'soh <product> <amount> <product> <amount>'")

class StockOnHandHandler(KeywordHandler):
    """
    Allows SMS reporters to send in "soh jd 10 mc 30" to report 10 jadelle, 30 male condoms
    """

    keyword = "soh"
    
    def help(self):
        if not hasattr(self.msg,'logistics_contact'):
            self.respond(_("You must REGISTER before you can submit a stock report." +
                           "Please text 'register <NAME> <FACILITY_CODE>'."))
            return
        self.respond(ERR_MSG)

    def handle(self, text):
        if not hasattr(self.msg,'logistics_contact'):
            self.respond(_("You must REGISTER before you can submit a stock report." +
                           "Please text 'register <NAME> <FACILITY_CODE>'."))
            return
        sdp = self.msg.logistics_contact.service_delivery_point
        stock_report = ProductStockReport(sdp, self.msg.logger_msg, STOCK_ON_HAND_REPORT_TYPE)
        stock_report.parse(text)
        if stock_report.errors:
            self.respond(_('You reported: %(stocks)s, but there were errors: %(err)s'),
                         stocks=", ". join(stock_report.product_stock),
                         err = ", ".join(unicode(e) for e in stock_report.errors))
            return
        all_products = []
        
        date_check = datetime.now() + relativedelta(days=-7)

        # check for products missing
        missing_products = Product.objects.filter(Q(productstock__service_delivery_point=sdp, productstock__is_active=True),
                                                  ~Q(productreport__report_date__gt=date_check) )
        for dict in missing_products.values('sms_code'):
            all_products.append(dict['sms_code'])
        missing_product_list = list(set(all_products)-stock_report.reported_products())
        low_supply = stock_report.low_supply()
        received = stock_report.received_products()
        if missing_product_list:
            kwargs = {'contact_name': self.msg.contact.name,
                      'facility_name': sdp.name,
                      'product_list': ', '.join(missing_product_list)}
            self.respond(_('Thank you %(contact_name)s for reporting your stock on hand for %(facility_name)s.  Still missing %(product_list)s.'), **kwargs)
        elif stock_report.has_stockout:
            self.respond(_('The following items are stocked out: %(stocks)s. Please place an order now.'), stocks=stock_report.stockouts())
        elif low_supply:
            self.respond(_('The following items are in low supply: %(stocks)s. Please place an order now.'), stocks=low_supply)
        elif received:
            self.respond(_('Thank you, you reported you have %(stocks)s. You received %(received)s. If incorrect, please resend.'),
                         stocks=stock_report.all(), received=stock_report.received())
        else:
            self.respond(_('Thank you, you reported you have %(stocks)s. If incorrect, please resend.'), stocks=stock_report.all())

        # notify the supervisor
        sdp.supervisor_report(stock_report)

