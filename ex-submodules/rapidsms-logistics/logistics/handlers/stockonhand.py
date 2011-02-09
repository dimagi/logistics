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
from logistics.apps.logistics.models import ServiceDeliveryPoint, Product, ProductStock, ProductReportType

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

class ProductStockReport(object):
    """ The following is a helper class to make it easy to generate reports based on stock on hand """
    def __init__(self, sdp, message):
        self.product_stock = {}
        self.product_received = {}
        self.facility = sdp
        self.message = message
        self.has_stockout = False

    def parse(self, string):
        my_list = string.split()

        def getTokens(seq):
            for item in seq:
                yield item
        an_iter = getTokens(my_list)
        a = None
        try:
            while True:
                if a is None:
                    a = an_iter.next()
                b = an_iter.next()
                self.add_product_stock(a,b)
                c = an_iter.next()
                if c.isdigit():
                    self.add_product_receipt(a,c)
                    a = None
                else:
                    a = c
        except StopIteration:
            pass
        return

    def add_product_stock(self, product, stock, save=True):
        if isinstance(stock, basestring) and stock.isdigit():
            stock = int(stock)
        if not isinstance(stock,int):
            raise TypeError("stock must be reported in integers")
        stock = int(stock)
        self.product_stock[product] = stock
        if stock == 0:
            self.has_stockout = True
        if save:
            self._record_product_stock(product, stock)

    def _record_product_stock(self, product_code, quantity):
        report_type = ProductReportType.objects.get(slug='soh')
        try:
            product = Product.objects.get(sms_code__contains=product_code)
        except Product.DoesNotExist:
            raise ValueError(_("Sorry, invalid product code %(code)s"), code=product_code.upper())
        self.facility.report(product=product, report_type=report_type,
                                           quantity=quantity, message=self.message)

    def reported_products(self):
        reported_products = []
        for i in self.product_stock:
            reported_products.append(i)
        return set(reported_products)

    def add_product_receipt(self, product, receipt):
        if isinstance(stock, basestring) and stock.isdigit():
            stock = int(stock)
        if not isinstance(stock,int):
            raise TypeError("stock must be reported in integers")
        self.product_received[product] = int(stock)

    def all(self):
        reply_list = []
        for i in self.product_stock:
            reply_list.append('%s %s' % (i, self.product_stock[i]))
        return ', '.join(reply_list)

    def stockouts(self):
        stocked_out = ""
        for i in self.product_stock:
            if self.product_stock[i] == 0:
                stocked_out = "%s %s" % (stocked_out, i)
        stocked_out = stocked_out.strip()
        return stocked_out

    def low_supply(self):
        self.facility
        low_supply = ""
        for i in self.product_stock:
            productstock = ProductStock.objects.filter(service_delivery_point=self.facility).get(product__sms_code__contains=i)
            if self.product_stock[i] < productstock.monthly_consumption:
                low_supply = "%s %s" % (low_supply, i)
        low_supply = low_supply.strip()
        return low_supply

    def over_supply(self):
        return NotImplementedError
