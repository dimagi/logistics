#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from rapidsms.conf import settings
from logistics.models import ProductReportsHelper, ProductStock
from logistics.const import Reports
from logistics.models import Validator
from logistics.template_app import App as LogisticsApp
from logistics.util import config

class DoNothingValidator(Validator):
    def validate(self, supply_point, product_stock=None, product_received=None, consumption=None):
        return

class SohAndReceiptValidator(Validator):
    def validate(self, supply_point, product_stock=None, product_received=None, consumption=None):
        product_stock = {} if product_stock is None else product_stock
        product_received = {} if product_received is None else product_received
        consumption = {} if consumption is None else consumption
        self._validate_no_stock_increase_without_receipt(supply_point, 
                                                         product_stock, 
                                                         product_received, 
                                                         consumption)
        self._validate_receipts(supply_point, product_stock, product_received, consumption)

    def _validate_receipts(self, supply_point, product_stock, product_received, consumption):
        errors = {}
        if len(product_received) < len(product_stock):
            errors = []
            for product in product_stock:
                if product not in product_received:
                    errors.append(product)
            if errors:
                didumean = " ".join("%s%s.0"%(product, product_stock[product]) for product in errors)
                raise ValueError(config.Messages.NO_RECEIPT_ERROR % {'didumean': didumean})
    def _validate_no_stock_increase_without_receipt(self, supply_point, product_stock, 
                                                         product_received, consumption):
        errors = {}
        for product in product_stock:
            try:
                ps = ProductStock.objects.get(supply_point=supply_point, 
                                              product__sms_code=product)
            except ProductStock.DoesNotExist:
                return
            if ps.quantity is not None and ps.quantity < product_stock[product]:
                stock_increase = product_stock[product] - ps.quantity
                if product not in product_received or product_received[product] == 0:
                    errors[product] = [product_stock[product], stock_increase]
        if errors:
            didumean = " ".join("%s%s.%s"%(product, errors[product][0],errors[product][1]) for product in errors)
            raise ValueError(config.Messages.NO_RECEIPT_ON_STOCK_INCREASE_ERROR % {'didumean': didumean})

class App(LogisticsApp):
    def handle (self, message):
        should_proceed, return_code = self._check_preconditions(message)
        if not should_proceed:
            return return_code
        try:
            message.text = self._clean_message(message.text)
            stock_report = ProductReportsHelper(message.logistics_contact.supply_point, 
                                                Reports.SOH, message.logger_msg, 
                                                validator=DoNothingValidator())
            stock_report.parse(message.text)
            try:
                stock_report.validate()
            except ValueError, e:
                # we don't want to fail on validation errors, just detect & report
                stock_report.errors.append(e)
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
        
