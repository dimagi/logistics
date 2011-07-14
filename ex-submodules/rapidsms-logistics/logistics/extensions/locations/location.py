from __future__ import absolute_import
from django.db import models
from django.db.models import Q
import uuid

class Location(models.Model):
    """
    Location - the main concept of a location.  Currently covers MOHSW, Regions, Districts and Facilities.
    This could/should be broken out into subclasses.
    """
    code = models.CharField(max_length=100, blank=False, null=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True
        
    def peers(self):
        from rapidsms.contrib.locations.models import Location
        return Location.objects.filter(parent_id=self.parent_id).order_by('name')
    
    def get_children(self):
        """ This signature gets overriden by mptt when mptt is used """
        from rapidsms.contrib.locations.models import Location
        return Location.objects.filter(parent_id=self.id).order_by('name')

    def facilities(self):
        from logistics.models import SupplyPoint
        return SupplyPoint.objects.filter(location=self, active=True).order_by('name')

    def child_facilities(self):
        from logistics.models import SupplyPoint
        return SupplyPoint.objects.filter(Q(location=self)|Q(location__parent_id=self.pk), active=True).order_by('name')
    
    def get_descendents(self, include_self=False):
        """ This signature gets overriden by mptt when mptt is used
        It must return a queryset
        """
        from rapidsms.contrib.locations.models import Location
        def _get_descendent_pks(node):
            pks = []
            for c in node.get_children():
                pks.append(c.pk)
                pks.extend(_get_descendent_pks(c))
            return pks
        pks = _get_descendent_pks(self)
        if include_self:
            pks.append(self.pk)
        ret = Location.objects.filter(id__in=pks)
        return ret

    def all_facilities(self):
        from logistics.models import SupplyPoint
        locations = self.get_descendents(include_self=True)
        return SupplyPoint.objects.filter(location__in=locations, active=True).order_by('name')
    
    def all_child_facilities(self):
        from logistics.models import SupplyPoint
        locations = self.get_descendents()
        return SupplyPoint.objects.filter(location__in=locations, active=True).order_by('name')
        
    """ The following methods express AGGREGATE counts, of all subsumed facilities"""
    def stockout_count(self, product=None, producttype=None):
        from logistics.models import stockout_count
        return stockout_count(self.all_facilities(), product, producttype)

    def emergency_stock_count(self, product=None, producttype=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        from logistics.models import emergency_stock_count
        return emergency_stock_count(self.all_facilities(), product, producttype)

    def low_stock_count(self, product=None, producttype=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        from logistics.models import low_stock_count
        return low_stock_count(self.all_facilities(), product, producttype)

    def emergency_plus_low(self, product=None, producttype=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        from logistics.models import emergency_plus_low
        return emergency_plus_low(self.all_facilities(), product, producttype)

    def good_supply_count(self, product=None, producttype=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        from logistics.models import good_supply_count
        return good_supply_count(self.all_facilities(), product, producttype)

    def overstocked_count(self, product=None, producttype=None):
        from logistics.models import overstocked_count
        return overstocked_count(self.all_facilities(), product, producttype)

    def consumption(self, product=None, producttype=None):
        from logistics.models import consumption
        return consumption(self.all_facilities(), product, producttype)

    def deprecate(self, new_code=None):
        """
        Deprecates a location, by changing the code and deactivating it.
        """
        if new_code is None:
            new_code = "deprecated-%s-%s" % (self.code, uuid.uuid4()) 
        self.code = new_code
        self.is_active = False
        self.save()
