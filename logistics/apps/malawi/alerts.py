from datetime import datetime, timedelta
from logistics.apps.alerts import Alert
from logistics.apps.logistics.models import StockRequest, SupplyPoint
from django.db.models.aggregates import Max
from django.core.urlresolvers import reverse


class LateReportingAlert(Alert):
    
    def __init__(self, supply_point, last_responded):
        self._supply_point = supply_point
        self._last_responded = last_responded
        super(LateReportingAlert, self).__init__(self._get_text(), self._get_url())
    
    def _get_text(self):
        return "%(person)s got an 'order ready' alert on %(date)s but has still not reported a receipt." % \
                {"person": self.supply_point.name,
                 "date": self.last_responded.strftime('%d-%B-%Y')}
    
    def _get_url(self):
        return reverse("logistics_dashboard", args=[self.supply_point.code])
        
        
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
    