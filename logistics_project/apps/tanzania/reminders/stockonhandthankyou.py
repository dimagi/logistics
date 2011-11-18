from scheduler.decorators import businessday_before
from logistics.util import config
from datetime import datetime, timedelta
from logistics_project.apps.tanzania.reminders import send_reminders
from logistics_project.apps.tanzania.config import SupplyPointCodes
from rapidsms.models import Contact
from logistics.const import Reports
from dimagi.utils.dates import get_business_day_of_month

def get_people(cutoff):
    # these go out every month to every active person at all facilities
    # who has reported this month
    for contact in Contact.objects.filter\
            (supply_point__type__code=SupplyPointCodes.FACILITY):
        if contact.supply_point.productreport_set.filter\
                (report_type__code=Reports.SOH,
                 report_date__gte=cutoff).exists():
            yield contact

def get_cutoff(year, month):
    return get_business_day_of_month(year, month, -1)

def last_yearmonth():
    now = datetime.utcnow()
    last_month = datetime(now.year, now.month, 1) - timedelta(days=1)
    return (last_month.year, last_month.month)

@businessday_before(20)
def first():
    """Last business day before the 20th at 4:00 PM"""
    people = get_people(get_cutoff(*last_yearmonth()))
    send_reminders(people,
                   config.Messages.SOH_THANK_YOU)