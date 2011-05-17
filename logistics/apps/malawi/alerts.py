from datetime import datetime, timedelta
from logistics.apps.alerts import Alert
from logistics.apps.logistics.models import StockRequest, SupplyPoint,\
    SupplyPointType
from django.db.models.aggregates import Max
from django.core.urlresolvers import reverse
from logistics.apps.logistics.util import config


class LateReportingAlert(Alert):
    
    def __init__(self, supply_point, last_responded):
        self._supply_point = supply_point
        self._last_responded = last_responded
        super(LateReportingAlert, self).__init__(self._get_text(), _supply_point_url(supply_point))
    
    def _get_text(self):
        return "%(person)s got an 'order ready' alert on %(date)s but has still not reported a receipt." % \
                {"person": self.supply_point.name,
                 "date": self.last_responded.strftime('%d-%B-%Y')}
    
    @property
    def supply_point(self):
        return self._supply_point
    
    @property
    def last_responded(self):
        return self._last_responded
    
    
def late_reporting_receipt():
    """
    7 days after the "order ready" has been sent to the HSA
    if there is still no reported receipt an alert shows up.
    """
    # this means that there is a stock request with 
    # status of "ready" that hasn't been modified in > 7 days
    since = datetime.utcnow() - timedelta(days=7)
    bad_reqs = StockRequest.objects.filter(received_on=None, responded_on__lte=since)\
                    .values('supply_point').annotate(last_response=Max('responded_on'))
    alerts = [LateReportingAlert(SupplyPoint.objects.get(pk=val["supply_point"]), val["last_response"]) \
              for val in bad_reqs]
    return alerts

def hsas_no_supervision():
    """
    HSAs working out of facilities that don't have any registered
    in charges or managers.
    """
    hsas = SupplyPoint.objects.filter(type=SupplyPointType.objects.get(code="hsa"))
    facilities_with_hsas = set(hsas.values_list("supplied_by", flat=True))
    orphaned_facilities = SupplyPoint.objects.exclude\
        (contact__role__code__in=config.Roles.SUPERVISOR_ROLES)
    orphaned_facilities_with_hsas = orphaned_facilities.filter(pk__in=facilities_with_hsas)
    return [Alert("No in charge or supervisor is registered for %s but there are HSAs there." % fac, _supply_point_url(fac)) \
            for fac in orphaned_facilities_with_hsas]
    
    
def _supply_point_url(supply_point):
    return reverse("logistics_dashboard", args=[supply_point.code])


