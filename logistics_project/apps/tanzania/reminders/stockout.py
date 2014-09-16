from datetime import datetime, timedelta
from dimagi.utils.dates import get_day_of_month
from logistics.const import Reports
from logistics_project.apps.tanzania.config import SupplyPointCodes
from rapidsms.models import Contact
from logistics.util import config
from django.utils.translation import ugettext_noop as _
from scheduler.decorators import businessday


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


@businessday(6)
def first():
    people = get_people(get_cutoff(*last_yearmonth()))
    for person in people:
        stocked_out = set(person.supply_point.stockout_products().keys())
        if stocked_out:
            overstocked_str = ""
            for sp in person.supply_point.closest_supply_points.all():
                overstocked = set(sp.overstocked_products().keys())
                intersection = overstocked.intersection(stocked_out)
                if intersection:
                    overstocked_str += "%s (%s)" % (sp.name, ', '.join(intersection))
            if overstocked_str:
                print _(config.Messages.REMINDER_STOCKOUT) % {'products_list': ', '.join(stocked_out),
                                                              'overstocked_list': overstocked_str}