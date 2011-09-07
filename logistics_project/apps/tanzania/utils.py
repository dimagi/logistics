from datetime import datetime,timedelta, time
from re import match
from django.db.models.aggregates import Max
from logistics_project import settings
from logistics_project.apps.tanzania.models import SupplyPointStatus, DeliveryGroups,\
    SupplyPointStatusValues, SupplyPointStatusTypes, OnTimeStates, DeliveryGroupReport
from logistics.models import SupplyPoint, ProductReport, ProductReportType
from logistics.const import Reports
from dimagi.utils.dates import get_business_day_of_month, get_business_day_of_month_before
import logging

logger = logging.getLogger(__name__)

def chunks(l, n):
    """
    Yield chunks of size <n> of list <l>
    http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def latest_status(sp, type, value=None, month=None, year=None):
    qs = sp.supplypointstatus_set.filter(status_type=type)
    if value:
        qs = qs.filter(status_value=value)
    if month and year:
        qs = qs.filter(status_date__month=month, status_date__year=year)
    qs = qs.order_by("-status_date")
    return qs[0] if qs.count() else None

def sps_with_latest_status(sps, status_type, status_value, year, month):
    """
    This method is used by the dashboard.
    """
    # filter out people who submitted in the wrong month
    if status_type.startswith('rr'):
        sps = DeliveryGroups(month).submitting(sps, month)
    elif status_type.startswith('del'):
        sps = DeliveryGroups(month).delivering(sps, month)
    if not sps.count():
        return SupplyPoint.objects.none()
    inner = sps.filter(supplypointstatus__status_type=status_type,
                       supplypointstatus__status_value=status_value,
                       supplypointstatus__status_date__month=month,
                       supplypointstatus__status_date__year=year)\
                        .annotate(max_sp_status_id=Max('supplypointstatus__id'))
    ids = SupplyPointStatus.objects.filter(id__in=inner.values('max_sp_status_id').query)\
                                           .distinct()\
                                            .values_list("supply_point", flat=True)
    f = sps.filter(id__in=ids)

    # I don't trust this method _at all_.  Here's some debug stuff. -- cternus
    
    for a in f:
        q = latest_status(a, status_type, value=status_value, year=year, month=month)
        if q and q.status_type != status_type or q.status_value != status_value:
            logger.error("false positive in sps_with_latest_status: %s %s %s" % (q, status_type, status_value))
    for s in sps:
        q = latest_status(s, status_type, value=status_value, year=year, month=month)
        if q and s not in f:
            logger.error("false negative in sps_with_latest_status: %s %s %s" % (s, status_type, status_value))
    return f

def supply_points_with_latest_status_by_datespan(sps, status_type, status_value, datespan):
    """
    This very similar method is used by the reminders.
    """
    inner = sps.filter(supplypointstatus__status_type=status_type,
                       supplypointstatus__status_date__gte=datespan.startdate,
                       supplypointstatus__status_date__lte=datespan.enddate)\
                        .annotate(pk=Max('supplypointstatus__id'))
    ids = SupplyPointStatus.objects.filter(id__in=inner.values('pk').query, 
                                           status_type=status_type,
                                           status_value=status_value)\
                                           .distinct()\
                                            .values_list("supply_point", flat=True)
    return SupplyPoint.objects.filter(id__in=ids)


def soh(sp, product, month=None, year=None):
    ProductReport.objects.filter(type=Reports.SOH)

def calc_lead_time(supply_point, year=None, month=None):
    """
    The days elapsed from the day they respond "submitted" to the day they 
    respond "delivered". Only include the last period for now
    """
    deliveries = SupplyPointStatus.objects.filter\
                        (supply_point=supply_point, 
                         status_type__in=[SupplyPointStatusTypes.DELIVERY_FACILITY,
                                          SupplyPointStatusTypes.DELIVERY_DISTRICT],
                         status_value=SupplyPointStatusValues.RECEIVED).order_by("-status_date")
    if year and month:
        deliveries.filter(status_date__month=month, status_date__year=year)

    if deliveries:
        latest_delivery = deliveries[0]
        previous_submissions = SupplyPointStatus.objects.filter\
                            (supply_point=supply_point, 
                             status_type__in=[SupplyPointStatusTypes.R_AND_R_FACILITY,
                                              SupplyPointStatusTypes.R_AND_R_DISTRICT],
                             status_value=SupplyPointStatusValues.SUBMITTED,
                             status_date__lte=latest_delivery.status_date).order_by("-status_date")
        if previous_submissions:
            lead_time = latest_delivery.status_date - previous_submissions[0].status_date
            if lead_time < timedelta(days=100):
                # if it's more than 100 days it's likely the wrong cycle
                return lead_time

def get_user_location(user):
    """
    Get a user's location, based on their user profile, return nothing if
    no location found.
    """
    if user and user.is_authenticated(): 
        prof = user.get_profile()
        if prof:
            return prof.location if prof.location else \
                prof.supply_point.location if prof.supply_point \
                else None

def last_stock_on_hand(facility):
    return last_stock_on_hand_before(facility, datetime.utcnow())

def last_stock_on_hand_before(facility, date):
    reports = ProductReport.objects.filter(supply_point=facility,
                                           report_type__code=Reports.SOH,
                                           report_date__lt=date)\
                                           .order_by('-report_date')
    return reports[0] if reports.exists() else None

def last_status_before(facility, date, type, value=None):
    statuses = SupplyPointStatus.objects.filter(supply_point=facility,
                                           status_type=type,
                                           status_date__lt=date)
    if value:
        statuses = statuses.filter(status_value=value)
    statuses= statuses.order_by('-status_date')

    return statuses[0] if statuses.exists() else None

def soh_reported_on_time(supply_point, year, month):
    last_bd_of_the_month = get_business_day_of_month(year, month, -1)
    last_report = last_stock_on_hand_before(supply_point, last_bd_of_the_month)
    last_of_last_month = datetime(year, month, 1) - timedelta(days=1)
    last_bd_of_last_month = datetime.combine\
       (get_business_day_of_month(last_of_last_month.year,
                                   last_of_last_month.month,
                                   -1), time())
    if last_report:
        return _reported_on_time(last_bd_of_last_month, last_report.report_date)
    else:
        return OnTimeStates.NO_DATA

def randr_reported_on_time(supply_point, year, month):
    reminder_date = datetime.combine(get_business_day_of_month_before(year, month, 5), time())
#    last_report = last_status_before(supply_point, get_business_day_of_month(year, month, -1), SupplyPointStatusTypes.R_AND_R_FACILITY, value=SupplyPointStatusValues.SUBMITTED)
    last_report = last_status_before(supply_point, datetime(year=year, month=month+1, day=1)-timedelta(days=1), SupplyPointStatusTypes.R_AND_R_FACILITY, value=SupplyPointStatusValues.SUBMITTED)
    if last_report:
        return _reported_on_time(reminder_date, last_report.status_date)

    else:
        return OnTimeStates.NO_DATA

def _reported_on_time(reminder_date, last_report_date):
    cutoff_date = reminder_date + timedelta(days=5)
    if last_report_date < reminder_date:
        return OnTimeStates.INSUFFICIENT_DATA
    elif last_report_date < cutoff_date:
        return OnTimeStates.ON_TIME
    else:
        return OnTimeStates.LATE

def soh_on_time_reporting(supply_points, year, month):
    return [f for f in supply_points if soh_reported_on_time(f, year, month) == OnTimeStates.ON_TIME]

def randr_on_time_reporting(supply_points, year, month):
    return [f for f in supply_points if randr_reported_on_time(f, year, month) == OnTimeStates.ON_TIME]


def submitted_to_msd(districts, month, year):
    count = 0
    for f in districts:
        dg = DeliveryGroupReport.objects.filter(report_date__month=month, report_date__year=year, supply_point=f).order_by("-date")
        if dg and dg.count():
            count += dg[0].quantity
    return count

def historical_response_rate(supply_point, type):
    statuses = SupplyPointStatus.objects.filter(supply_point=supply_point, status_type=type).order_by("-status_date")
    if not statuses.count(): return None
    status_month_years = set([(x.status_date.month, x.status_date.year) for x in statuses])
    denom = len(status_month_years)
    num = 0
    for s in status_month_years:
        f = statuses.filter(status_date__month=s[0], status_date__year=s[1]).order_by("-status_date")
        if f.count(): f = f[0]
        if f.status_value == SupplyPointStatusValues.SUBMITTED or f.status_value == SupplyPointStatusValues.RECEIVED:
            num += 1
    return float(num)/float(denom), num, denom

