from datetime import datetime,timedelta
from re import match
from django.db.models.aggregates import Max
from logistics_project.apps.tanzania.models import SupplyPointStatus, DeliveryGroups,\
    SupplyPointStatusValues, SupplyPointStatusTypes
from logistics.models import SupplyPoint, ProductReport, ProductReportType
from logistics.const import Reports


def chunks(l, n):
    """
    Yield chunks of size <n> of list <l>
    http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def sps_with_latest_status(sps, status_type, status_value, year, month):
    """
    This method is used by the dashboard.
    """
    # filter out people who submitted in the wrong month
    if status_type.startswith('rr'):
        sps = DeliveryGroups(month).submitting(sps, month)
    elif status_type.startswith('del'):
        sps = DeliveryGroups(month).delivering(sps, month)
    inner = sps.filter(supplypointstatus__status_type=status_type,
                       supplypointstatus__status_date__month=month,
                       supplypointstatus__status_date__year=year)\
                        .annotate(pk=Max('supplypointstatus__id'))
    ids = SupplyPointStatus.objects.filter(id__in=inner.values('pk').query, status_type=status_type,
                                           status_value=status_value)\
                                           .distinct()\
                                            .values_list("supply_point", flat=True)
    return SupplyPoint.objects.filter(id__in=ids)

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

def latest_status(sp, type, value=None, month=None, year=None):
    qs = sp.supplypointstatus_set.filter(status_type=type)
    if value:
        qs = qs.filter(status_value=value)
    if month and year:
        qs = qs.filter(status_date__month=month, status_date__year=year)
    qs = qs.order_by("-status_date")
    return qs[0] if qs.count() else None

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
