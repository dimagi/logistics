""" 
These scheduled reminders are, for now, super custom
"""

import logging
from rapidsms.conf import settings
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from rapidsms.contrib.messaging.utils import send_message
from rapidsms.messages.outgoing import OutgoingMessage
from logistics.apps.logistics.models import Contact, ProductReport
from django.utils.translation import ugettext as _
from logistics.apps.logistics.util import config
from rapidsms.conf import settings

######################
# Callback Functions #
######################

def first_soh_reminder (router):
    """ thusday reminders """
    logging.info("running first soh reminder")
    reporters = Contact.objects.filter(role__responsibilities__code=config.Responsibilities.STOCK_ON_HAND_RESPONSIBILITY).distinct()
    reporters = reporters.filter(needs_reminders=True)
    for reporter in reporters:
        response = config.Messages.STOCK_ON_HAND_REMINDER % {'name':reporter.name}
        send_message_safe(reporter, response)

def second_soh_reminder (router):
    """monday follow-up"""
    logging.info("running second soh reminder")
    reporters = Contact.objects.filter(role__responsibilities__code=config.Responsibilities.STOCK_ON_HAND_RESPONSIBILITY).distinct()
    for reporter in reporters:
        latest_reports = ProductReport.objects.filter(supply_point=reporter.supply_point).order_by('-report_date')
        # TODO get this to vary alongside scheduled time
        deadline = datetime.now() + relativedelta(days=-5)
        if not latest_reports or latest_reports[0].report_date < deadline:
            response = config.Messages.SECOND_STOCK_ON_HAND_REMINDER % {'name':reporter.name}
            send_message_safe(reporter, response)

def third_soh_to_super (router):
    """ wednesday, message the in-charge """
    reporters = Contact.objects.filter(role__responsibilities__code=config.Responsibilities.STOCK_ON_HAND_RESPONSIBILITY).distinct()
    for reporter in reporters:
        latest_reports = ProductReport.objects.filter(supply_point=reporter.supply_point).order_by('-report_date')
        deadline = datetime.now() + relativedelta(days=-settings.LOGISTICS_DAYS_UNTIL_LATE_PRODUCT_REPORT)
        if not latest_reports or latest_reports[0].report_date < deadline:
            def _notify_super(supply_point, message):
                if reporter.supply_point is not None:
                    supers = Contact.objects.filter(supply_point=supply_point)
                    supers = supers.filter(role__responsibilities__code=config.Responsibilities.REPORTEE_RESPONSIBILITY).distinct()
                    for super in supers:
                        response = message % {'name':super.name, 'facility':supply_point.name }
                        send_message_safe(super, response)
            _notify_super(reporter.supply_point, config.Messages.THIRD_STOCK_ON_HAND_REMINDER)
            if reporter.supply_point:
                _notify_super(reporter.supply_point.supervised_by, config.Messages.THIRD_CHPS_STOCK_ON_HAND_REMINDER)                
        
def reminder_to_submit_RRIRV(router):
    """ the 30th of each month, verify that they've submitted RRIRV """
    logging.info("running RRIRV reminder")
    reporters = Contact.objects.filter(role__responsibilities__code=config.Responsibilities.STOCK_ON_HAND_RESPONSIBILITY).distinct()
    for reporter in reporters:
        response = config.Messages.RRIRV_REMINDER % {'name':reporter.name}
        send_message_safe(reporter, response)

def send_message_safe(contact, message):
    if contact.default_connection:
        OutgoingMessage(contact.default_connection, message).send()
