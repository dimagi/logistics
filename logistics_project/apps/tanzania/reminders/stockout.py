from datetime import datetime, timedelta
from dimagi.utils.dates import get_day_of_month
from logistics.const import Reports
from logistics_project.apps.tanzania.config import SupplyPointCodes
from models import Contact
from scheduler.decorators import day


#TODO move to utils
def get_people(cutoff):
    # these go out every month to every active person at all facilities
    # who has reported this month
    for contact in Contact.objects.filter\
            (supply_point__type__code=SupplyPointCodes.FACILITY, supply_point__is_pilot=True, is_active=True):
        if contact.supply_point.productreport_set.filter\
                (report_type__code=Reports.SOH,
                 report_date__gte=cutoff).exists():
            yield contact


def get_cutoff(year, month):
    return get_day_of_month(year, month, -1)


def last_yearmonth():
    now = datetime.utcnow()
    last_month = datetime(now.year, now.month, 1) - timedelta(days=1)
    return last_month.year, last_month.month


@day(6)
def sixth_day():
    people = get_people(get_cutoff(*last_yearmonth()))
    #TODO
