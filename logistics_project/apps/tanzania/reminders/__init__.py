"""
All facilities in the same group get the same reminders on the same schedule.
All districts get the same reminders on the same schedule.

Reminders can fire up to three times.
 - For all reminders, the second and third are only sent if the previous ones 
   have not been submitted.
 - The text of all three reminders is the same for each category of reminder.
 
"""
from rapidsms.contrib.messaging.utils import send_message
from django.utils.translation import ugettext as _

def send_reminders(contacts, message):
    for contact in contacts:
        send_message(contact.connection, _(message))