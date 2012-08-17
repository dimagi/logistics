from __future__ import absolute_import
from django.core.urlresolvers import reverse
from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown
from rapidsms.models import Contact
from alerts import Alert
from logistics.util import config
from logistics.models import ProductStock, SupplyPoint
from logistics.decorators import place_in_request, return_if_place_not_set
from django.utils.translation import ugettext as _

class SupplyPointStatusAlert(Alert):
    
    def __init__(self, sps):
        self.sps = sps
        self.bd = SupplyPointStatusBreakdown(facilities=sps)
    
    def _get_template(self):
        raise NotImplementedError("Subclasses should override this!")
    
    def get_count(self):
        raise NotImplementedError("Subclasses should override this!")
    
    @property
    def text(self):
        return _(self._get_template()) % {'count': self.get_count()}

    @property
    def url(self):
        return reverse('ordering')
    
class RandRNotSubmitted(SupplyPointStatusAlert):
    
    def _get_template(self):
        return '%(count)d facilities have reported not submitting their R&R form as of today.'
    
    def get_count(self):
        return len(self.bd.not_submitted)

def _alert_list(cls, facilities):
    if facilities:
        alert = cls(facilities)
        if alert.get_count():
            return [alert]
    
        
@place_in_request()
@return_if_place_not_set()
def randr_not_submitted(request):
    facilities = request.location.all_child_facilities()
    return _alert_list(RandRNotSubmitted, facilities)
    
class RandRNotResponded(SupplyPointStatusAlert):
    
    def _get_template(self):
        return '%(count)d facilities did not respond to the SMS asking if they had submitted their R&R form.'
    
    def get_count(self):
        return len(self.bd.submit_not_responding)

@place_in_request()
@return_if_place_not_set()
def randr_not_responded(request):
    facilities = request.location.all_child_facilities()
    return _alert_list(RandRNotResponded, facilities)
    
class DeliveryNotReceived(SupplyPointStatusAlert):
    
    def _get_template(self):
        return '%(count)d facilities have reported not receiving their deliveries as of today.'
    
    def get_count(self):
        return len(self.bd.delivery_not_received)

@place_in_request()
@return_if_place_not_set()
def delivery_not_received(request):
    facilities = request.location.all_child_facilities()
    return _alert_list(DeliveryNotReceived, facilities)
    
class DeliveryNotResponding(SupplyPointStatusAlert):
    
    def _get_template(self):
        return '%(count)d facilities did not respond to the SMS asking if they had received their delivery.'
    
    def get_count(self):
        return len(self.bd.delivery_reminder_sent)

@place_in_request()
@return_if_place_not_set()
def delivery_not_responding(request):
    facilities = request.location.all_child_facilities()
    return _alert_list(DeliveryNotResponding, facilities)
    
class SOHNotResponding(SupplyPointStatusAlert):
    def _get_template(self):
        return '%(count)d facilities have not reported their stock levels for last month.'
    
    def get_count(self):    
        return len(self.bd.soh_not_responding)
    
    @property
    def url(self):
        return reverse('facilities_index')
        
@place_in_request()
@return_if_place_not_set()
def soh_not_responding(request):
    facilities = request.location.all_child_facilities()
    return _alert_list(SOHNotResponding, facilities)
    
class ProductStockout(Alert):
    def __init__(self, sp, product):
        self.sp = sp
        self.product = product
        super(ProductStockout, self).__init__(self._get_text())

    def _get_text(self):
        return _('%(name)s is stocked out of %(product)s.') % {'name': self.sp.name, 'product': self.product.name}

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
        return _('%(name)s has no primary contact.') % {'name': self.sp.name}

@place_in_request()
@return_if_place_not_set()
def no_primary_contact(request):
    facilities = request.location.all_child_facilities().filter(contact=None)
    if not facilities:
        return None
    return [NoPrimaryContact(f) for f in facilities]







