import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from rapidsms.contrib.messaging.utils import send_message
from logistics.apps.logistics.models import LogisticsContact
from django.utils.translation import ugettext as _

######################
# Callback Functions #
######################

STOCK_ON_HAND_RESPONSIBILITY = 'reporter'
STOCK_ON_HAND_REMINDER = _('Please submit your soh by Friday at 2:00 pm.')
SECOND_STOCK_ON_HAND_REMINDER = _('Please submit your soh by Friday at 2:00 pm.')

def first_soh_reminder (router):
    reporters = LogisticsContact.objects.filter(role__responsibilities__slug=STOCK_ON_HAND_RESPONSIBILITY).distinct()
    for reporter in reporters:
        if reporter.needs_reminders:
            send_message(reporter.connection, STOCK_ON_HAND_REMINDER)
            #check for success?

def second_soh_reminder (router):
    reporters = LogisticsContact.objects.filter(role__responsibilities__slug=STOCK_ON_HAND_RESPONSIBILITY).distinct()
    for reporter in reporters:
        latest_report = ProductReport.objects.filter(service_delivery_point=reporter.service_delivery_point).order_by('-report_date')[0]
        # TODO get this to vary alongside scheduled time
        five_days_ago = datetime.now() + relativedelta(days=-5)
        if latest_report.report_date < five_days_ago:
            send_message(reporter.connection, SECOND_STOCK_ON_HAND_REMINDER)
            #check for success?


