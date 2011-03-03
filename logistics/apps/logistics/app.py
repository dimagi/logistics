#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.utils.translation import ugettext as _
from rapidsms.apps.base import AppBase
from rapidsms.contrib.scheduler.models import EventSchedule, set_weekly_event
from logistics.apps.logistics.models import Product, ProductReportsHelper, \
    STOCK_ON_HAND_REPORT_TYPE
from logistics.apps.logistics.models import REGISTER_MESSAGE

ERR_MSG = _("Please send your stock on hand in the format 'soh <product> <amount> <product> <amount>'")

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
        SOH_KEYWORD = 'soh'
        # catch this message only if it begins with 'soh' or one of the product codes
        keywords = [SOH_KEYWORD]
        keywords.extend(Product.objects.values_list('sms_code', flat=True).order_by('sms_code'))
        is_a_match = False
        text = message.text.lower()
        for keyword in keywords:
            if text.startswith(keyword):
                is_a_match = True
        if not is_a_match:
            return False

        try:
            if not hasattr(message,'logistics_contact'):
                message.respond(REGISTER_MESSAGE)
                return True
            message.text = message.text.lower()
            if message.text.startswith(SOH_KEYWORD):
                message.text = message.text.strip(SOH_KEYWORD)
            sdp = message.logistics_contact.facility
            if sdp is None:
                message.respond('You are not associated with a facility. ' +
                                'Please contact your district administrator for assistance.')
                return True
            stock_report = ProductReportsHelper(sdp, STOCK_ON_HAND_REPORT_TYPE, message.logger_msg)
            stock_report.parse(message.text)
            stock_report.save()
            if stock_report.errors:
                if stock_report.product_stock:
                    message.respond(_('You reported: %(stocks)s, but there were errors: %(err)s'),
                                 stocks=", ". join(stock_report.product_stock),
                                 err = ", ".join(unicode(e) for e in stock_report.errors))
                else:
                    message.respond(_('%(err)s'),
                                 err = ", ".join(unicode(e) for e in stock_report.errors))
                return True
            all_products = []
            date_check = datetime.now() + relativedelta(days=-7)
            # check for products missing
            missing_products = Product.objects.filter(Q(productstock__facility=sdp,
                                                        productstock__is_active=True),
                                                      ~Q(productreport__report_date__gt=date_check) )
            for dict in missing_products.values('sms_code'):
                all_products.append(dict['sms_code'])
            missing_product_list = list(set(all_products)-stock_report.reported_products())
            received = stock_report.received_products()
            low_supply = stock_report.low_supply()
            over_supply = stock_report.over_supply()
            count = 0
            response = ''
            super_response = ''
            if stock_report.has_stockout:
                response = response + 'the following items are stocked out: %(stockouts)s. '
                super_response = "stockouts %(stockouts)s; "
            if low_supply:
                response = response + 'the following items are in low supply: %(low_supply)s. '
                super_response = super_response + "low supply %(low_supply)s; "
            if stock_report.has_stockout or low_supply:
                response = response + 'Please place an order now. '
            if missing_product_list:
                if not response:
                    response = response + 'thank you for reporting your stock on hand. '
                response = response + 'Still missing %(missing_stock)s. '
            if over_supply:
                super_response = super_response + "overstocked %(overstocked)s; "
                if not response:
                    response = 'the following items are overstocked: %(overstocked)s. The district admin has been informed.'
            if not response:
                if received:
                    response = 'thank you for reporting the commodities you have. You received %(received)s.'
                else:
                    response = 'thank you for reporting the commodities you have in stock.'
            response = 'Dear %(name)s, ' + response.strip()
            if super_response:
                super_response = 'Dear %(admin_name)s, %(facility)s is experiencing the following problems: ' + super_response.strip().strip(';')
            kwargs = {  'low_supply':low_supply,
                        'stockouts':stock_report.stockouts(),
                        'missing_stock':', '.join(missing_product_list),
                        'stocks':stock_report.all(),
                        'received':stock_report.received(),
                        'overstocked':over_supply,
                        'name':message.contact.name,
                        'facility':sdp.name }
            message.respond(response, **kwargs)
            # notify the supervisor
            if super_response:
                sdp.report_to_supervisor(super_response, kwargs)
            return True

        except Exception, e:
            message.respond(unicode(e))
            raise

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