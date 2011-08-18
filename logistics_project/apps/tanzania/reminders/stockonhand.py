from scheduler.decorators import businessday
from logistics.util import config
from datetime import datetime, timedelta
from logistics_project.apps.tanzania.reminders import send_reminders
from logistics_project.apps.tanzania.config import SupplyPointCodes
from rapidsms.models import Contact
from logistics.const import Reports

def get_people():
    # these go out every month to every active person at all facilities
    # unless they've already submitted a SOH report this month.
    
    # TODO, change totally arbitrary cutoff
    cutoff = datetime.utcnow() - timedelta(days=10)
    for contact in Contact.objects.filter\
            (supply_point__code=SupplyPointCodes.FACILITY):
        if not contact.supply_point.product_report__set.filter\
                (report_type__code=Reports.SOH,
                 report_date__gte=cutoff).exists():
            yield contact
                

@businessday(-1)
def first():
    """Last business day of the month-2:00 PM"""
    send_reminders(get_people(), config.Messages.REMINDER_STOCKONHAND)
    
@businessday(1)
def second():
    """1st business day of the next month – 9:00am"""
    send_reminders(get_people(), config.Messages.REMINDER_STOCKONHAND)
    
@businessday(5)
def third():
    """5th  business day of the next month – 8:15am"""
    send_reminders(get_people(), config.Messages.REMINDER_STOCKONHAND)
    

    
    