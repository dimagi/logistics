"""
All facilities in the same group get the same reminders on the same schedule.
All districts get the same reminders on the same schedule.

Reminders can fire up to three times.
 - For all reminders, the second and third are only sent if the previous ones
   have not been submitted.
 - The text of all three reminders is the same for each category of reminder.

"""
from django.conf import settings
from django.utils.translation import ugettext as _
from datetime import datetime
from threadless_router.router import Router
from rapidsms import router

def send_message(contact, message, **kwargs):
    # this hack sets the global router to threadless router.
    # should maybe be cleaned up.
    if not settings.UNIT_TESTING:
        router.router = Router()
    contact.message(message, **kwargs)

def send_reminders(contacts, message):
    for contact in contacts:
        if contact.default_connection and contact.is_active:
            send_message(contact, _(message))

def update_statuses(contacts, type, value):
    # hack: import happens here to prevent tasks import error
    from logistics_project.apps.tanzania.models import SupplyPointStatus

    now = datetime.utcnow()
    for sp in set(c.supply_point for c in contacts):
        SupplyPointStatus.objects.create(supply_point=sp,
                                         status_type=type,
                                         status_value=value,
                                         status_date=now)
