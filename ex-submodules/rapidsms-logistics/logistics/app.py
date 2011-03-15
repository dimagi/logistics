#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

"""
The main purpose of this app is to parse reports of stock on hand and receipts
Look at the unit tests for specific examples.
"""

import re
from rapidsms.conf import settings
from django.utils.translation import ugettext as _
from rapidsms.apps.base import AppBase
from rapidsms.contrib.scheduler.models import EventSchedule, set_weekly_event
from logistics.apps.logistics.models import Product, ProductReportsHelper, \
    STOCK_ON_HAND_REPORT_TYPE, GET_HELP_MESSAGE
from logistics.apps.logistics.models import REGISTER_MESSAGE

ERR_MSG = _("Please send your stock on hand in the format 'soh <product> <amount> <product> <amount>'")
SOH_KEYWORD = 'soh'

class App(AppBase):
    bootstrapped = False

    def start (self):
        """Configure your app in the start phase."""
        if not self.bootstrapped:
            self.bootstrapped = True
            
            # set up first soh reminder
            try:
                EventSchedule.objects.get(callback="logistics.schedule.first_soh_reminder")
            except EventSchedule.DoesNotExist:
                # 2:15 pm on Thursdays
                set_weekly_event("logistics.schedule.first_soh_reminder",3,14,15)

            # set up second soh reminder
            try:
                EventSchedule.objects.get(callback="logistics.schedule.second_soh_reminder")
            except EventSchedule.DoesNotExist:
                # 2:15 pm on Mondays
                set_weekly_event("logistics.schedule.second_soh_reminder",0,14,15)

    def parse (self, message):
        """Parse and annotate messages in the parse phase."""
        pass

    def handle (self, message):
        """Add your main application logic in the handle phase."""
        if not self._should_handle(message):
            return False
        if not hasattr(message,'logistics_contact'):
            message.respond(REGISTER_MESSAGE)
            return True
        sdp = message.logistics_contact.facility
        if sdp is None:
            message.respond('You are not associated with a facility. ' +
                            'Please contact your district administrator for assistance.')
            return True

        try:
            message.text = self._clean_message(message.text)
            stock_report = ProductReportsHelper(sdp, STOCK_ON_HAND_REPORT_TYPE, message.logger_msg)
            stock_report.parse(message.text)
            stock_report.save()
            if stock_report.errors:
                if stock_report.product_stock:
                    message.respond(_('You reported: %(stocks)s, but there were errors: %(err)s'),
                                 stocks=", ". join(stock_report.product_stock),
                                 err = "".join(unicode(e) for e in stock_report.errors))
                else:
                    message.respond(_('%(err)s'),
                                 err = "".join(unicode(e) for e in stock_report.errors))
                return True
            (response, super_response, kwargs) = stock_report.get_responses()
            message.respond(response, **kwargs)
            if super_response:
                sdp.report_to_supervisor(super_response, kwargs, exclude=[message.logistics_contact])
            return True

        except Exception, e:
            message.respond(unicode(e))
            raise
    
    def default(self, message):
        """ There's probably a better way to do this, but for now,
        this is what the folks in the field want 
        """
        match = re.search("[0-9]", message.text)
        if match is not None:
            index = message.text.find(match.group(0))
            code = message.text[:index].strip()
            message.error("%s is not a recognized commodity code. " % code + 
                          "Please contact FRHP for assistance." )
        elif settings.DEFAULT_RESPONSE is not None:
            message.error(settings.DEFAULT_RESPONSE,
                          project_name=settings.PROJECT_NAME)

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
        """ Tests whether this message is one which should go through the handle phase
        i.e. if it begins with soh or one of the product codes """
        keywords = [SOH_KEYWORD]
        keywords.extend(Product.objects.values_list('sms_code', flat=True).order_by('sms_code'))
        text = message.text.lower()
        for keyword in keywords:
            if text.startswith(keyword):
                return True
        return False

    def _clean_message(self, text):
        text = text.lower()
        if text.startswith(SOH_KEYWORD):
            return text.strip(SOH_KEYWORD)
        return text

