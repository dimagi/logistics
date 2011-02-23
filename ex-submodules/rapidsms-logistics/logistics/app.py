#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.utils.translation import ugettext as _
from rapidsms.apps.base import AppBase
from rapidsms.contrib.scheduler.models import EventSchedule, set_weekly_event
from logistics.apps.logistics.models import Product, ProductStockReport, \
    STOCK_ON_HAND_REPORT_TYPE

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
                message.respond(_("You must REGISTER before you can submit a stock report." +
                               "Please text 'register <NAME> <FACILITY_CODE>'."))
                return
            message.text = message.text.lower()
            if message.text.startswith(SOH_KEYWORD):
                message.text = message.text.strip(SOH_KEYWORD)
            sdp = message.logistics_contact.location
            stock_report = ProductStockReport(sdp, STOCK_ON_HAND_REPORT_TYPE, message.logger_msg)
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
                return
            all_products = []
            date_check = datetime.now() + relativedelta(days=-7)
            # check for products missing
            missing_products = Product.objects.filter(Q(productstock__location=sdp,
                                                        productstock__is_active=True),
                                                      ~Q(productreport__report_date__gt=date_check) )
            for dict in missing_products.values('sms_code'):
                all_products.append(dict['sms_code'])
            missing_product_list = list(set(all_products)-stock_report.reported_products())
            low_supply = stock_report.low_supply()
            received = stock_report.received_products()
            if missing_product_list:
                kwargs = {'contact_name': message.contact.name,
                          'facility_name': sdp.name,
                          'product_list': ', '.join(missing_product_list)}
                message.respond(_('Thank you %(contact_name)s for reporting your stock on hand for %(facility_name)s.  Still missing %(product_list)s.'), **kwargs)
            elif stock_report.has_stockout:
                message.respond(_('The following items are stocked out: %(stocks)s. Please place an order now.'), stocks=stock_report.stockouts())
            elif low_supply:
                message.respond(_('The following items are in low supply: %(stocks)s. Please place an order now.'), stocks=low_supply)
            elif received:
                message.respond(_('Thank you, you reported you have %(stocks)s. You received %(received)s. If incorrect, please resend.'),
                             stocks=stock_report.all(), received=stock_report.received())
            else:
                message.respond(_('Thank you, you reported you have %(stocks)s. If incorrect, please resend.'), stocks=stock_report.all())

            # notify the supervisor
            sdp.supervisor_report(stock_report)
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