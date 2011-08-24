from datetime import datetime,timedelta
from re import match
from django.db.models.aggregates import Max
from logistics_project.apps.tanzania.models import SupplyPointStatus, DeliveryGroups
from logistics.models import SupplyPoint

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
