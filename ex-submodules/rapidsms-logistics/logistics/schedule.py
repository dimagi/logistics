""" 
These scheduled reminders are, for now, super custom
"""

import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from rapidsms.contrib.messaging.utils import send_message
from rapidsms.messages.outgoing import OutgoingMessage
from logistics.apps.logistics.models import Contact, \
    STOCK_ON_HAND_RESPONSIBILITY, REPORTEE_RESPONSIBILITY, \
    ProductReport, CHPS_TYPE
from django.utils.translation import ugettext as _

######################
# Callback Functions #
######################

STOCK_ON_HAND_REMINDER = _('Hi %(name)s! Please text your stock report tomorrow Friday by 2:00 pm. Your stock report can help save lives.')
SECOND_STOCK_ON_HAND_REMINDER = _('Hi %(name)s, we did not receive your stock report last Friday. Please text your stock report as soon as possible.')
THIRD_STOCK_ON_HAND_REMINDER = _('Dear %(name)s, your facility has not reported its stock this week. Please make sure that the SMS stock report is submitted.')
THIRD_CHPS_STOCK_ON_HAND_REMINDER = _('Dear %(name)s, %(facility)s has not reported its stock this week. Please make sure that the SMS stock report is submitted.')
RRIRV_REMINDER = _("Dear %(name)s, have you submitted your stock requisition this month? Please reply 'yes' or 'no'")

def first_soh_reminder (router):
    """ thusday reminders """
    logging.info("running first soh reminder")
    reporters = Contact.objects.filter(role__responsibilities__code=STOCK_ON_HAND_RESPONSIBILITY).distinct()
    reporters = reporters.filter(needs_reminders=True)
    for reporter in reporters:
        response = STOCK_ON_HAND_REMINDER % {'name':reporter.name}
        send_message(reporter, response)

def second_soh_reminder (router):
    """monday follow-up"""
    logging.info("running second soh reminder")
    reporters = Contact.objects.filter(role__responsibilities__code=STOCK_ON_HAND_RESPONSIBILITY).distinct()
    for reporter in reporters:
        latest_reports = ProductReport.objects.filter(supply_point=reporter.supply_point).order_by('-report_date')
        # TODO get this to vary alongside scheduled time
        five_days_ago = datetime.now() + relativedelta(days=-5)
        if not latest_reports or latest_reports[0].report_date < five_days_ago:
            response = SECOND_STOCK_ON_HAND_REMINDER % {'name':reporter.name}
            send_message(reporter, response)

def third_soh_to_super (router):
    """ wednesday, message the in-charge """
    reporters = Contact.objects.filter(role__responsibilities__code=STOCK_ON_HAND_RESPONSIBILITY).distinct()
    for reporter in reporters:
        latest_reports = ProductReport.objects.filter(supply_point=reporter.supply_point).order_by('-report_date')
        five_days_ago = datetime.now() + relativedelta(days=-7)
        if not latest_reports or latest_reports[0].report_date < five_days_ago:
            supers = Contact.objects.filter(supply_point=reporter.supply_point)
            supers = supers.filter(role__responsibilities__code=REPORTEE_RESPONSIBILITY).distinct()
            for super in supers:
                response = THIRD_STOCK_ON_HAND_REMINDER % {'name':super.name}
                send_message(super, response)
            # custom code it so that the supervisor of the supply_point supplying the CHPS
            # gets the escalation message. we cannot reuse these reminders for tz.
            if reporter.supply_point.type.code == CHPS_TYPE:
                super_supers = Contact.objects.filter(supply_point=reporter.supply_point.supplied_by)
                super_supers = super_supers.filter(role__responsibilities__code=REPORTEE_RESPONSIBILITY).distinct()
                for super_super in super_supers:
                    response = THIRD_CHPS_STOCK_ON_HAND_REMINDER % {'name':super_super.name, 
                                                                    'facility':reporter.supply_point }
                    send_message(super_super, response)
                
        
def reminder_to_submit_RRIRV(router):
    """ the 30th of each month, verify that they've submitted RRIRV """
    logging.info("running RRIRV reminder")
    reporters = Contact.objects.filter(role__responsibilities__code=STOCK_ON_HAND_RESPONSIBILITY).distinct()
    reporters = reporters.filter(needs_reminders=True)
    for reporter in reporters:
        response = RRIRV_REMINDER % {'name':reporter.name}
        send_message(reporter, response)

def send_message(contact, message):
    if contact.default_connection:
        OutgoingMessage(contact.default_connection, message).send()
    