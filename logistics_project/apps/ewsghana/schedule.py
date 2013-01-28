""" 
These scheduled reminders are, for now, super custom
"""

import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from rapidsms.conf import settings
from rapidsms.contrib.messaging.utils import send_message
from rapidsms.messages.outgoing import OutgoingMessage
from logistics.models import Contact, \
    ProductReport, SupplyPoint, LogisticsProfile
from logistics.util import config

######################
# Callback Functions #
######################

def first_soh_reminder (router):
    """ thusday reminders """
    logging.info("running first soh reminder")
    reporters = Contact.objects.filter(role__responsibilities__code=config.Responsibilities.STOCK_ON_HAND_RESPONSIBILITY, 
                                       is_active=True).distinct()
    reporters = reporters.filter(needs_reminders=True)
    for reporter in reporters:
        response = config.Messages.STOCK_ON_HAND_REMINDER % {'name':reporter.name}
        send_message_safe(reporter, response)

def second_soh_reminder (router):
    """monday follow-up"""
    logging.info("running second soh reminder")
    reporters = Contact.objects.filter(role__responsibilities__code=config.Responsibilities.STOCK_ON_HAND_RESPONSIBILITY, 
                                       is_active=True).distinct()
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
    facilities = SupplyPoint.active_objects.all()
    for facility in facilities:
        if facility.contact_set.count() == 0:
            continue
        on_time_products, missing_products = facility.report_status()
        def _notify_web_super(facility_to_notify, about, message, products=[]):
            profiles = LogisticsProfile.objects.exclude(contact=None)\
                                               .exclude(contact__connection=None)\
                                               .filter(supply_point=facility_to_notify, 
                                                       sms_notifications=True)\
                                               .select_related('contact', 'contact__connection')
            for profile in profiles:
                super = profile.contact
                response = message % {'name':super.name, 'facility':about.name, 
                                      'products':", ".join([prod.name for prod in products]) if products else None }
                send_message_safe(super, response)
        def _notify_super(facility_to_notify, about, message, products=[]):
            if facility_to_notify is not None:
                supers = facility_to_notify.reportees()
                for super in supers:
                    response = message % {'name':super.name, 'facility':about.name, 
                                          'products':", ".join([prod.name for prod in products]) if products else None }
                    send_message_safe(super, response)
        if not on_time_products:
            # alert to super: no stock reports received
            _notify_super(facility, facility, config.Messages.THIRD_STOCK_ON_HAND_REMINDER)
            _notify_web_super(facility, facility, config.Messages.THIRD_STOCK_ON_HAND_REMINDER)
            _notify_super(facility.supervised_by, facility, config.Messages.THIRD_STOCK_ON_HAND_REMINDER)
        elif missing_products:
            # alert to super: not all stock reports received
            _notify_super(facility, facility, config.Messages.INCOMPLETE_SOH_TO_SUPER, missing_products)
            _notify_web_super(facility, facility, config.Messages.INCOMPLETE_SOH_TO_SUPER, missing_products)
            _notify_super(facility.supervised_by, facility, config.Messages.INCOMPLETE_SOH_TO_SUPER, missing_products)
        
def stockout_notification_to_web_supers(router):
    """ wednesday, message the web-based supervisors about stockouts """
    profiles = LogisticsProfile.objects.exclude(contact=None)\
                                       .exclude(contact__connection=None)\
                                       .filter(sms_notifications=True)\
                                       .filter(supply_point__active=True)\
                                       .filter(supply_point__productstock__quantity=0).distinct()\
                                       .select_related('contact', 'contact__connection')
    for profile in profiles:
        stockouts = profile.supply_point.products_stocked_out
        date = profile.supply_point.last_reported.strftime('%b %d') if profile.supply_point.last_reported else None
        response = config.Messages.STOCKOUT_REPORT % {'name':profile.contact.name, 
                                                      'facility':profile.supply_point.name, 
                                                      'date':date, 
                       'products':", ".join([prod.name for prod in stockouts]) if stockouts else None }
        send_message_safe(profile.contact, response)
        
def reminder_to_submit_RRIRV(router):
    """ the 30th of each month, verify that they've submitted RRIRV """
    logging.info("running RRIRV reminder")
    reporters = Contact.objects.filter(role__responsibilities__code=config.Responsibilities.STOCK_ON_HAND_RESPONSIBILITY, 
                                       is_active=True).distinct()
    for reporter in reporters:
        response = config.Messages.RRIRV_REMINDER % {'name':reporter.name}
        send_message_safe(reporter, response)

        
def reminder_to_visit_website(router):
    logging.info("running website reminder")
    web_users = User.objects.filter(is_active=True, logisticsprofile__sms_notifications=True).\
                filter(last_login__lte=datetime.now()-timedelta(weeks=13)).\
                exclude(logisticsprofile__contact__connection=None).\
                filter(logisticsprofile__location__type__slug__in=(config.LocationCodes.COUNTRY, 
                                                                  config.LocationCodes.REGION, 
                                                                  config.LocationCodes.DISTRICT))
    for user in web_users:
        prof = user.get_profile()
        response = config.Messages.WEB_REMINDER % {'name':prof.name()}
        send_message_safe(prof.contact, response)

def send_message_safe(contact, message):
    if contact.default_connection:
        OutgoingMessage(contact.default_connection, message).send()
