#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
The main purpose of this app is to parse reports of stock on hand and receipts
Look at the unit tests for specific examples.
"""

import re
from rapidsms.conf import settings
from django.utils.importlib import import_module
from django.utils.translation import ugettext as _
from rapidsms.apps.base import AppBase
from logistics.models import Product, ProductReportsHelper
from logistics.errors import UnknownCommodityCodeError
from logistics.const import Reports
from logistics.util import config

class App(AppBase):

    def start (self):
        """Configure your app in the start phase."""
        pass

    def parse (self, message):
        """Parse and annotate messages in the parse phase."""
        pass

    def _check_preconditions(self, message):
        """
        Handles base logic of whether this message should be processed.
        Returns a tuple, the first value is whether the operation should
        proceed with the normal handle phase, the second being the return 
        code. If the first argument is True, the value of the second argument 
        is not defined.
        """
        if not self._should_handle(message):
            return (False, False)
        if not hasattr(message,'logistics_contact'):
            message.respond(config.Messages.REGISTER_MESSAGE)
            return (False, True)
        if message.logistics_contact.supply_point is None:
            message.respond(config.Messages.NO_SUPPLY_POINT_MESSAGE)
            return (False, True)
        if not self._clean_message(message.text):
            message.respond(config.Messages.SOH_HELP_MESSAGE)
            return (False, True)
        return (True, None)
        
    def _send_error_response(self, message, stock_report):
        kwargs = {}
        if stock_report.product_stock:
            kwargs['stocks'] = ", ". join(stock_report.product_stock)
            error_message = 'You reported: %(stocks)s, but there were errors: %(err)s'
        else:
            error_message = '%(err)s'
        missing = stock_report.missing_products()
        if missing:
            kwargs['missing'] = ", ".join(missing)
            error_message = error_message + " Please report %(missing)s."
        kwargs['err'] = ", ".join(unicode(e) for e in stock_report.errors if not isinstance(e, UnknownCommodityCodeError))
        bad_codes = ", ".join(unicode(e) for e in stock_report.errors if isinstance(e, UnknownCommodityCodeError))
        kwargs['err'] = kwargs['err'] + "Unrecognized commodity codes: %(bad_codes)s." % {'bad_codes':bad_codes}
        error_message = ("{0} {1}".format(error_message, config.Messages.GET_HELP_MESSAGE)).strip()
        message.respond(error_message, **kwargs)
    
    def _get_responses(self, stock_report):
        """
        Gets responses to a SOH message, in the form of a response to the 
        sender, a response to the supervisor, and kwargs to populate them.
        """
        response = ''
        super_response = ''
        amount_to_reorder = stock_report.amount_to_reorder()
        stockouts = stock_report.stockouts()
        low_supply = stock_report.low_supply()
        over_supply = stock_report.over_supply()
        received = stock_report.nonzero_received()
        missing_product_list = stock_report.missing_products()
        if missing_product_list:
            response = response + 'still missing %(missing_stock)s. '
        if stockouts:
            response = response + 'these items are stocked out: %(stockouts)s. '
            super_response = "stockouts %(stockouts)s; "
        if low_supply:
            response = response + 'these items need to be reordered: %(low_supply)s. '
            super_response = super_response + "below reorder level %(low_supply)s; "
        if (stockouts or low_supply) and amount_to_reorder:
            response = response + 'Please order %(amount_to_reorder)s. '
        if over_supply:
            super_response = super_response + "overstocked %(overstocked)s; "
            if not response:
                response = 'these items are overstocked: %(overstocked)s. The district admin has been informed.'
        if not response:
            if received:
                response = 'thank you for reporting the commodities you have. You received %(received)s.'
            else:
                response = 'thank you for reporting the commodities you have in stock.'
        response = 'Dear %(name)s, ' + response.strip()
        if super_response:
            super_response = 'Dear %(admin_name)s, %(supply_point)s is experiencing the following problems: ' + super_response.strip().strip(';')
        kwargs = {  'low_supply': low_supply,
                    'stockouts': stockouts,
                    'amount_to_reorder': amount_to_reorder,
                    'missing_stock': ', '.join(missing_product_list),
                    'stocks': stock_report.all(),
                    'received': received,
                    'overstocked': over_supply,
                    'name': stock_report.message.contact.name,
                    'supply_point': stock_report.supply_point.name }
        return (response, super_response, kwargs)

    def _send_responses(self, message, stock_report):
        if stock_report.errors:
            self._send_error_response(message, stock_report)
        else:
            (response, super_response, kwargs) = self._get_responses(stock_report)
            message.respond(response, **kwargs)
            if super_response:
                message.logistics_contact.supply_point.report_to_supervisor\
                    (super_response, kwargs, exclude=[message.logistics_contact])

    def handle (self, message):
        """Add your main application logic in the handle phase."""
        should_proceed, return_code = self._check_preconditions(message)
        if not should_proceed:
            return return_code
        try:
            message.text = self._clean_message(message.text)
            stock_report = ProductReportsHelper(message.logistics_contact.supply_point, 
                                                Reports.SOH, message.logger_msg)
            stock_report.parse(message.text)
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

    def default(self, message):
        """
        If this implementation of RapidSMS supports message tagging,
        tag the message with a default tag.
        """
        if hasattr(message.logger_msg, "tags"):
            message.logger_msg.tags.add("Handler_DefaultHandler")
            if hasattr(message.connection, 'contact') and message.connection.contact:
                message.logger_msg.tags.add("RegisteredContact")
            else:
                message.logger_msg.tags.add("UnregisteredContact")
        
        """ complain if the first code isn't recognized as a commodity code 
        - but only on aggressive soh parsing
        """
        match = re.search("[0-9]", message.text)
        if match is not None and settings.LOGISTICS_AGGRESSIVE_SOH_PARSING and \
          hasattr(message.connection, 'contact'):
            index = message.text.find(match.group(0))
            code = message.text[:index].strip()
            if code:
                message.error(config.Messages.BAD_CODE_ERROR % {'code':code} )
                return
        if settings.DEFAULT_RESPONSE is not None:
            message.error(settings.DEFAULT_RESPONSE,
                          project_name=settings.PROJECT_NAME)
            return

    def cleanup (self, message):
        """Perform any clean up after all handlers have run in the
           cleanup phase."""
        pass

    def outgoing (self, message):
        """Handle outgoing message notifications."""
        pass

    def stop (self):
        """Perform global app cleanup when the application is stopped."""
        pass

    def _should_handle(self, message):
        """
        Tests whether this message is one which should go through the handle phase
        i.e. if it begins with soh or one of the product codes
        """
        if not settings.LOGISTICS_AGGRESSIVE_SOH_PARSING:
            return message.text.lower().startswith(Reports.SOH) 
        else:
            keywords = [Reports.SOH]
            keywords.extend(Product.objects.values_list('sms_code', flat=True).order_by('sms_code'))
            text = message.text.lower()
            for keyword in keywords:
                if text.startswith(keyword):
                    return True
            return False

        
    def _clean_message(self, text):
        text = text.lower()
        if text.startswith(Reports.SOH):
            return text.strip(Reports.SOH)
        return text

