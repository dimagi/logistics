from datetime import datetime, timedelta
from django.db.models.expressions import F
from logistics.apps.alerts import Alert
from logistics.apps.logistics.models import StockRequest, SupplyPoint,\
    SupplyPointType, _filtered_stock, ProductStock
from django.db.models.aggregates import Max
from django.core.urlresolvers import reverse
from logistics.apps.logistics.util import config
from logistics.apps.logistics.decorators import place_in_request
from logistics.apps.malawi.nag import get_non_reporting_hsas
from logistics.apps.malawi.util import get_facility_supply_points, hsas_below

class ProductStockAlert(Alert):

    def __init__(self, supply_point, product ):
        self._supply_point = supply_point
        self._product = product
        super(ProductStockAlert, self).__init__(self._get_text(), _hsa_url(supply_point))

    def _get_text(self):
        return "%(place)s is stocked out of %(product)s." % \
                {"place": self.supply_point.name,
                 "product": self.product.name}

    @property
    def supply_point(self):
        return self._supply_point

    @property
    def product(self):
        return self.product

def health_center_stockout(request):
    return [ProductStockAlert(stock.supply_point, stock.product) for stock in \
            ProductStock.objects.filter(is_active=True, supply_point__in=SupplyPoint.objects.filter(type__name="health facility")).filter(quantity=0)]

class HealthCenterUnableResupplyStockoutAlert(ProductStockAlert):

    def _get_text(self):
        return "%(hsa)s is stocked out of %(product)s and %(parent)s has inadequate supply." % \
                {"hsa": self.supply_point.name,
                 "parent": self.supply_point.supplied_by.name,
                 "product": self.product}

def health_center_unable_resupply_stockout(request):
    r = []
    for s in  StockRequest.pending_requests().all():
        if s.supply_point.supplied_by.type.name == "health facility" and \
           s.supply_point.supplied_by.stock(s.product) < s.amount_requested and \
           s.supply_point.stock(s.product) == 0:
                r += [HealthCenterUnableResupplyStockoutAlert(s.supply_point, s.product)]
    return r

class HealthCenterUnableResupplyEmergencyAlert(ProductStockAlert):

    def _get_text(self):
        return "%(hsa)s has an emergency order of %(product)s and %(parent)s has inadequate supply." % \
                {"hsa": self.supply_point.name,
                 "parent": self.supply_point.supplied_by.name,
                 "product": self.product}

def health_center_unable_resupply_emergency(request):
    r = []
    for s in  StockRequest.pending_requests().filter(is_emergency=True):
        if s.supply_point.supplied_by.type.name == "health facility" and \
           s.supply_point.supplied_by.stock(s.product) < s.amount_requested:
            r += [HealthCenterUnableResupplyEmergencyAlert(s.supply_point, s.product)]
    return r


class NonReportingHSAAlert(Alert):
    def __init__(self, hsa):
        self._hsa = hsa
        super(NonReportingHSAAlert, self).__init__(self._get_text(), _hsa_url(self.hsa))

    def _get_text(self):
        return "%(hsa)s has not reported in in the last month." % {'hsa': self.hsa.name}

    @property
    def hsa(self):
        return self._hsa

def non_reporting_hsas(request):
    return [NonReportingHSAAlert(hsa) for hsa in get_non_reporting_hsas(datetime.utcnow() - timedelta(days=32))]

class HSABelowEmergencyQuantityAlert(ProductStockAlert):
    def _get_text(self):
        return "%(hsa)s was restocked but remains below emergency quantity of %(product)s." % \
                {"hsa": self.supply_point.name,
                 "product": self.product.name}


def hsa_below_emergency_quantity(request):
    '''
    This query finds HSA/product pairs where the product is below emergency level but there are no pending requests.
    '''
    return [HSABelowEmergencyQuantityAlert(p.supply_point, p.product) for p in ProductStock.objects.filter(
            is_active=True,
            quantity__lte = F('product__emergency_order_level')).exclude(
                    supply_point__in=[r.supply_point for r in StockRequest.pending_requests()])]


class LateReportingAlert(Alert):
    
    def __init__(self, supply_point, last_responded):
        self._supply_point = supply_point
        self._last_responded = last_responded
        super(LateReportingAlert, self).__init__(self._get_text(), _hsa_url(supply_point))
    
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


@place_in_request()    
def late_reporting_receipt(request):
    """
    7 days after the "order ready" has been sent to the HSA
    if there is still no reported receipt an alert shows up.
    """
    # this means that there is a stock request with 
    # status of "ready" that hasn't been modified in > 7 days
    hsas = hsas_below(request.location)
    
    since = datetime.utcnow() - timedelta(days=7)
    bad_reqs = StockRequest.objects.filter(received_on=None, responded_on__lte=since, requested_by__in=hsas)\
                    .values('supply_point').annotate(last_response=Max('responded_on'))
    alerts = [LateReportingAlert(SupplyPoint.objects.get(pk=val["supply_point"]), val["last_response"]) \
              for val in bad_reqs]
    return alerts

@place_in_request()
def hsas_no_supervision(request):
    """
    HSAs working out of facilities that don't have any registered
    in charges or managers.
    """
    base_facilitities = get_facility_supply_points()
    if request.location:
        base_facilitities = SupplyPoint.objects.filter(location__parent_id=request.location.pk)
    hsas = SupplyPoint.objects.filter(type=SupplyPointType.objects.get(code="hsa"))
    facilities_with_hsas = set(hsas.values_list("supplied_by", flat=True))
    orphaned_facilities = base_facilitities.exclude\
        (contact__role__code__in=config.Roles.SUPERVISOR_ROLES)
    orphaned_facilities_with_hsas = orphaned_facilities.filter(pk__in=facilities_with_hsas)
    return [Alert("No in charge or supervisor is registered for %s but there are HSAs there." % fac, _facility_url(fac)) \
            for fac in orphaned_facilities_with_hsas]
    
    
def _facility_url(supply_point):
    return reverse("malawi_facility", args=[supply_point.code])

def _hsa_url(supply_point):
    return reverse("malawi_hsa", args=[supply_point.code])


