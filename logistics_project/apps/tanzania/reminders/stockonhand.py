from scheduler.decorators import businessday
from logistics.util import config
from datetime import datetime, timedelta
from logistics_project.apps.tanzania.reminders import send_reminders
from logistics_project.apps.tanzania.config import SupplyPointCodes
from rapidsms.models import Contact
from logistics.const import Reports
from dimagi.utils.dates import get_business_day_of_month_before
from logistics_project.apps.tanzania.models import SupplyPointStatusValues,\
    SupplyPointStatusTypes, SupplyPointStatus

def get_people(cutoff):
    # these go out every month to every active person at all facilities
    # unless they've already submitted a SOH report this month.
    
    for contact in Contact.objects.filter\
            (supply_point__type__code=SupplyPointCodes.FACILITY):
        if not contact.supply_point.productreport_set.filter\
                (report_type__code=Reports.SOH,
                 report_date__gte=cutoff).exists():
            yield contact
                
def get_cutoff(year, month):
    return get_business_day_of_month_before(year, month, -1)

def this_yearmonth():
    now = datetime.utcnow()
    return (now.year, now.month)

def last_yearmonth():
    now = datetime.utcnow()
    last_month = datetime(now.year, now.month, 1) - timedelta(days=1)
    return (last_month.year, last_month.month)
    
def update_statuses(contacts):
    now = datetime.utcnow()
    for sp in set(c.supply_point for c in contacts):
        SupplyPointStatus.objects.create(supply_point=sp,
                                         status_type=SupplyPointStatusTypes.SOH_FACILITY,
                                         status_value=SupplyPointStatusValues.REMINDER_SENT,
                                         status_date=now)
            
@businessday(-1)
def first():
    """Last business day of the month 2:00 PM"""
    people = get_people(get_cutoff(*this_yearmonth()))
    send_reminders(people, config.Messages.REMINDER_STOCKONHAND) 
    update_statuses(people)        
    
@businessday(1)
def second():
    """1st business day of the next month 9:00am"""
    people = get_people(get_cutoff(*last_yearmonth()))
    send_reminders(people, config.Messages.REMINDER_STOCKONHAND)
    update_statuses(people)
    
@businessday(5)
def third():
    """5th business day of the next month 8:15am"""
    people = get_people(get_cutoff(*last_yearmonth()))
    send_reminders(people, config.Messages.REMINDER_STOCKONHAND)
    update_statuses(people)
    

    
    