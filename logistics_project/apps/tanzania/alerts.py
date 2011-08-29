from __future__ import absolute_import
from django.core.urlresolvers import reverse
from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown
from rapidsms.models import Contact
from alerts import Alert
from logistics.util import config
from logistics.models import ProductStock
from logistics.decorators import place_in_request, return_if_place_not_set
from django.utils.translation import ugettext as _

# TODO Don't show these alerts if 0 facilities fall under that category.

class RandRNotSubmitted(Alert):
    def __init__(self, sps):
        self.sps = sps
        self.bd = SupplyPointStatusBreakdown(facilities=sps)
        super(RandRNotSubmitted, self).__init__(self._get_text, reverse('ordering'))

    def _get_text(self):
        return '%d facilities have reported not submitting their R&R form as of today.' % len(self.bd.not_submitted)

@place_in_request()
@return_if_place_not_set()
def randr_not_submitted(request):
    facilities = request.location.all_child_facilities()
    if not facilities:
        return None
    return [RandRNotSubmitted(facilities)]

class RandRNotResponded(Alert):
    def __init__(self, sps):
        self.sps = sps
        self.bd = SupplyPointStatusBreakdown(facilities=sps)
        super(RandRNotResponded, self).__init__(self._get_text(), reverse('ordering'))

    def _get_text(self):
        return '%s facilities did not respond to the SMS asking if they had submitted their R&R form.' % len(self.bd.not_responding)

@place_in_request()
@return_if_place_not_set()
def randr_not_responded(request):
    facilities = request.location.all_child_facilities()
    if not facilities:
        return None
    return [RandRNotResponded(facilities)]

class DeliveryNotReceived(Alert):
    def __init__(self, sps):
        self.sps = sps
        self.bd = SupplyPointStatusBreakdown(facilities=sps)
        super(DeliveryNotReceived, self).__init__(self._get_text(), reverse('ordering'))

    def _get_text(self):
        return '%s facilities have reported not receiving their deliveries as of today.' % len(self.bd.delivery_not_received)

@place_in_request()
@return_if_place_not_set()
def delivery_not_received(request):
    facilities = request.location.all_child_facilities()
    if not facilities:
        return None
    return [DeliveryNotReceived(facilities)]

class ProductStockout(Alert):
    def __init__(self, sp, product):
        self.sp = sp
        self.product = product
        super(ProductStockout, self).__init__(self._get_text())

    def _get_text(self):
        return '%s is stocked out of %s.' % (self.sp.name, self.product.name)

@place_in_request()
@return_if_place_not_set()
def product_stockout(request):
    facilities = request.location.all_child_facilities()
    stockouts = ProductStock.objects.filter(supply_point__in=facilities, quantity=0)
    if not facilities:
        return None
    return [ProductStockout(s.supply_point, s.product) for s in stockouts]

class NoPrimaryContact(Alert):
    def __init__(self, sp):
        self.sp = sp
        super(NoPrimaryContact, self).__init__(self._get_text())

    def _get_text(self):
        return '%s has no primary contact.' % (self.sp.name)

@place_in_request()
@return_if_place_not_set()
def no_primary_contact(request):
    facilities = request.location.all_child_facilities().filter(contact=None)
    if not facilities:
        return None
    return [NoPrimaryContact(f) for f in facilities]





