#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from rapidsms.conf import settings
from logistics.models import ProductReportsHelper, ProductStock
from logistics.const import Reports
from logistics.models import Validator
from logistics.template_app import App as LogisticsApp

class SohAndReceiptValidator(Validator):
    def validate(self, supply_point, product_stock={}, product_received={}, consumption={}):
        for stock in product_stock:
            try:
                ps = ProductStock.objects.get(supply_point=supply_point, 
                                              product__sms_code=stock)
            except ProductStock.DoesNotExist:
                return
            if ps.quantity and ps.quantity < product_stock[stock]:
                stock_increase = product_stock[stock] - ps.quantity
                if stock not in product_received or stock_increase > product_received[stock]:
                    raise ValueError('You reported an increase in %s ' % stock + 
                                     'without an associated receipt. Pls report receipt ' + 
                                     'in the format "[code] [stock on hand] [amount received]"')

class App(LogisticsApp):
    def handle (self, message):
        should_proceed, return_code = self._check_preconditions(message)
        if not should_proceed:
            return return_code
        try:
            message.text = self._clean_message(message.text)
            stock_report = ProductReportsHelper(message.logistics_contact.supply_point, 
                                                Reports.SOH, message.logger_msg, 
                                                validator=SohAndReceiptValidator())
            stock_report.parse(message.text)
            stock_report.validate()
            stock_report.save()
            self._send_responses(message, stock_report)
            return True
        except ValueError, e:
            # a parsing error, with a user-friendly message
            message.respond(unicode(e))
            return
        except Exception, e:
            # some other crazy error
            if settings.DEBUG:
                # this error actually gets logged deep within rapidSMS
                message.respond(unicode(e))
            raise
        
