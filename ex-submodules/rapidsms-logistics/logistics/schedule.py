import logging
from datetime import datetime, timedelta
from rapidsms.contrib.messaging.utils import send_message

######################
# Callback Functions #
######################

STOCK_ON_HAND_RESPONSIBILITY = 'reporter'
STOCK_ON_HAND_REMINDER = 'Please submit your soh by Friday at 2:00 pm.'

def first_soh_reminder (router):
    reporters = Contact.objects.filter(role__responsibilities__slug=STOCK_ON_HAND_RESPONSIBILITY).distinct()
    for reporter in reporters:
        send_message(reporter.connection, STOCK_ON_HAND_REMINDER)
        #check for success?

def second_soh_reminder (router):
    reporters = Contact.objects.filter(role__responsibilities__slug=STOCK_ON_HAND_RESPONSIBILITY).distinct()
    for reporter in reporters:
        send_message(reporter.connection, STOCK_ON_HAND_REMINDER)
        #check for success?
