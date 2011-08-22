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

def sps_with_latest_status(sps, status_type, status_value, report_date):
    """
    Filters S
    """
    if status_type.startswith('rr'):
        sdps = DeliveryGroups(report_date.month).submitting(sps, report_date.month)
    elif status_type.startswith('del'):
        sdps = DeliveryGroups(report_date.month).delivering(sps, report_date.month)
    inner = sps.filter(supplypointstatus__status_type=status_type,
#                       supplypointstatus__status_value=status_value,
                       supplypointstatus__status_date__month=report_date.month,
                       supplypointstatus__status_date__year=report_date.year)\
                        .annotate(pk=Max('supplypointstatus__id'))
    ids = SupplyPointStatus.objects.filter(id__in=inner.values('pk').query, status_type=status_type,
                                           status_value=status_value)\
                                           .distinct()\
                                            .values_list("supply_point", flat=True)
    return SupplyPoint.objects.filter(id__in=ids)

