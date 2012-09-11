#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import re
from rapidsms.conf import settings
from django.utils.importlib import import_module
from django.utils.translation import ugettext as _
from rapidsms.apps.base import AppBase
from logistics.models import Product, ProductReportsHelper
from logistics.errors import UnknownCommodityCodeError
from logistics.const import Reports
from logistics.util import config
from logistics.template_app import App as LogisticsApp

class App(LogisticsApp):
    def handle (self, message):
        """Add your main application logic in the handle phase."""
        print "Ghana handle"
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

