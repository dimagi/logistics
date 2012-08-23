""" 
These scheduled reminders are, for now, super custom
"""

import logging
from rapidsms.conf import settings
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from rapidsms.contrib.messaging.utils import send_message
from rapidsms.messages.outgoing import OutgoingMessage
from logistics.models import Contact, \
    ProductReport, SupplyPoint
from django.utils.translation import ugettext as _
from logistics.util import config
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
        if reporter.supply_point:
            on_time_products, missing_products = reporter.supply_point.report_status(days_until_late=5)
            if not on_time_products:
                response = config.Messages.SECOND_STOCK_ON_HAND_REMINDER % {'name':reporter.name}
                send_message_safe(reporter, response)
            elif missing_products:
                response = config.Messages.SECOND_INCOMPLETE_SOH_REMINDER % {'name':reporter.name, 
                                                                             'products':" ".join([prod.sms_code for prod in missing_products])}
                send_message_safe(reporter, response)

def third_soh_to_super (router):
    """ wednesday, message the in-charge """
    facilities = SupplyPoint.objects.all()
    for facility in facilities:
        if facility.contact_set.count() == 0:
            continue
        on_time_products, missing_products = facility.report_status()
        def _notify_super(facility_to_notify, about, message, products=[]):
            if facility_to_notify is not None:
                supers = Contact.objects.filter(supply_point=facility_to_notify)
                supers = supers.filter(role__responsibilities__code=config.Responsibilities.REPORTEE_RESPONSIBILITY).distinct()
                for super in supers:
                    response = message % {'name':super.name, 'facility':about.name, 
                                          'products':" ".join([prod.sms_code for prod in products]) if products else None }
                    send_message_safe(super, response)
        if not on_time_products:
            # alert to super: no stock reports received
            _notify_super(facility, facility, config.Messages.THIRD_STOCK_ON_HAND_REMINDER)
            _notify_super(facility.supervised_by, facility, config.Messages.THIRD_STOCK_ON_HAND_REMINDER)
        elif missing_products:
            # alert to super: not all stock reports received
            _notify_super(facility, facility, config.Messages.INCOMPLETE_SOH_TO_SUPER, missing_products)
            _notify_super(facility.supervised_by, facility, config.Messages.INCOMPLETE_SOH_TO_SUPER, missing_products)
            
        
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
