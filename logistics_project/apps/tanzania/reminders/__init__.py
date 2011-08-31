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
from datetime import datetime
from logistics_project.apps.tanzania.models import SupplyPointStatus

def send_reminders(contacts, message):
    for contact in contacts:
        send_message(contact.default_connection, _(message))
        
def update_statuses(contacts, type, value):
    now = datetime.utcnow()
    for sp in set(c.supply_point for c in contacts):
        SupplyPointStatus.objects.create(supply_point=sp,
                                         status_type=type,
                                         status_value=value,
                                         status_date=now)
