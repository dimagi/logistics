from __future__ import absolute_import
from __future__ import unicode_literals
from datetime import datetime, timedelta
from django.db.models.expressions import F
from alerts import Alert
from logistics.models import StockRequest, SupplyPoint,\
    SupplyPointType, ProductStock, StockRequestStatus
from django.db.models.aggregates import Max
from django.core.urlresolvers import reverse
from logistics.util import config
from logistics.decorators import place_in_request
from logistics_project.apps.malawi.nag import get_non_reporting_hsas
from logistics_project.apps.malawi.util import get_facility_supply_points, hsas_below,\
    hsa_supply_points_below, facility_supply_points_below, get_managed_products_for_contact
from logistics_project.apps.malawi.templatetags.malawi_tags import place_url

class ProductStockAlert(Alert):

    def __init__(self, supply_point, product ):
        self._supply_point = supply_point
        self._product = product
        super(ProductStockAlert, self).__init__(self._get_text(), place_url(supply_point.location))

    def _get_text(self):
        return "%(place)s is stocked out of %(product)s." % \
                {"place": self.supply_point.name,
                 "product": self.product.name}

    @property
    def supply_point(self):
        return self._supply_point

    @property
    def product(self):
        return self._product

@place_in_request()
def health_center_stockout(request):
    sps = facility_supply_points_below(request.location)
    return [ProductStockAlert(stock.supply_point, stock.product) for stock in \
            ProductStock.objects.filter(is_active=True, supply_point__in=sps).filter(quantity=0)]

class HealthCenterUnableResupplyStockoutAlert(ProductStockAlert):

    def _get_text(self):
        return "%(hsa)s is stocked out of %(product)s and %(parent)s cannot fill order." % \
                {"hsa": self.supply_point.name,
                 "parent": self.supply_point.supplied_by.name,
                 "product": self.product}

@place_in_request()
def health_center_unable_resupply_stockout(request):
    r = []
    hsas = hsa_supply_points_below(request.location)
    for s in StockRequest.pending_requests().filter(supply_point__in=hsas,
                                                    status=StockRequestStatus.STOCKED_OUT):
        if s.supply_point.stock(s.product) == 0:
            r += [HealthCenterUnableResupplyStockoutAlert(s.supply_point, s.product)]
    return r

class HealthCenterUnableResupplyEmergencyAlert(ProductStockAlert):

    def _get_text(self):
        return "%(hsa)s has an emergency order of %(product)s and %(parent)s cannot fill order." % \
                {"hsa": self.supply_point.name,
                 "parent": self.supply_point.supplied_by.name,
                 "product": self.product}

@place_in_request()
def health_center_unable_resupply_emergency(request):
    hsas = hsa_supply_points_below(request.location)
    return [HealthCenterUnableResupplyEmergencyAlert(s.supply_point, s.product)\
            for s in StockRequest.pending_requests()\
                            .filter(is_emergency=True,
                                    status=StockRequestStatus.STOCKED_OUT,
                                    supply_point__in=hsas)]
    

class NonReportingHSAAlert(Alert):
    def __init__(self, hsa):
        self._hsa = hsa
        super(NonReportingHSAAlert, self).__init__(self._get_text(), _hsa_url(self.hsa))

    def _get_text(self):
        return "%(hsa)s has not reported in the last month." % {'hsa': self.hsa.name}

    @property
    def hsa(self):
        return self._hsa

@place_in_request()
def non_reporting_hsas(request):
    return [NonReportingHSAAlert(hsa) for hsa in get_non_reporting_hsas(datetime.utcnow() - timedelta(days=32),
                                                                        location=request.location)]

class HSABelowEmergencyQuantityAlert(ProductStockAlert):
    def _get_text(self):
        return "%(hsa)s was resupplied but remains below emergency quantity of %(product)s." % \
                {"hsa": self.supply_point.name,
                 "product": self.product.name}

@place_in_request()
def hsa_below_emergency_quantity(request):
    '''
    This query finds HSA/product pairs where the product is below emergency level but there are no pending requests.
    '''
    hsas = hsa_supply_points_below(request.location)
    r = []
    for p in ProductStock.objects.filter(is_active=True,
            supply_point__in=hsas,
            quantity__lte = F('product__emergency_order_level')):
        if not StockRequest.pending_requests().filter(product=p.product, supply_point=p.supply_point).exists():
            r += [HSABelowEmergencyQuantityAlert(p.supply_point, p.product)]
    return r


class LateReportingAlert(Alert):
    
    def __init__(self, supply_point, last_responded):
        self._supply_point = supply_point
        self._last_responded = last_responded
        super(LateReportingAlert, self).__init__(self._get_text(), _hsa_url(supply_point))
    
    def _get_text(self):
        return "%(person)s got an 'order ready' message on %(date)s but has still not reported a receipt." % \
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
    hsas = hsa_supply_points_below(request.location)
    
    since = datetime.utcnow() - timedelta(days=7)
    bad_reqs = StockRequest.objects.filter(received_on=None, responded_on__lte=since, 
                                           supply_point__in=hsas,
                                           status=StockRequestStatus.APPROVED)\
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
    base_facilitities = facility_supply_points_below(request.location)
    
    hsas = SupplyPoint.objects.filter(active=True, type=SupplyPointType.objects.get(code="hsa"))
    facilities_with_hsas = hsas.values_list("supplied_by", flat=True).distinct()
    orphaned_facilities = base_facilitities.exclude\
        (contact__role__code__in=config.Roles.HSA_SUPERVISOR_ROLES)
    orphaned_facilities_with_hsas = orphaned_facilities.filter(pk__in=facilities_with_hsas)
    return [Alert(config.Alerts.FACILITY_NO_SUPERVISOR % {"facility": fac}, _facility_url(fac)) \
            for fac in orphaned_facilities_with_hsas]

@place_in_request()
def hsas_no_products(request):
    hsas = hsas_below(request.location)
    return [Alert(config.Alerts.HSA_NO_PRODUCTS % {"hsa": hsa.name}, _hsa_url(hsa.supply_point)) \
                  for hsa in hsas.all() if get_managed_products_for_contact(hsa).count() == 0]
    
def _facility_url(supply_point):
    return reverse("malawi_facility", args=[supply_point.code])

def _hsa_url(supply_point):
    return reverse("malawi_hsa", args=[supply_point.code])


