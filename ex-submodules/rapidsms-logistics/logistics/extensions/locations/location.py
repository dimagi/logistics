from __future__ import absolute_import
import uuid
from django.db import models
from django.db.models import Q
from django.conf import settings
from logistics.mixin import StockCacheMixin

class Location(models.Model, StockCacheMixin):
    """
    Location - the main concept of a location.  Currently covers MOHSW, Regions, Districts and Facilities.
    This could/should be broken out into subclasses.
    """
    code = models.CharField(max_length=100, blank=False, null=False)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True
    
    def set_parent(self, parent):
        if hasattr(self,'tree_parent'):
            self.tree_parent = parent
        else:
            self.parent = parent
        self.save()
        
    @property
    def tree_parent(self):
        """ This signature gets overriden by mptt when mptt is used """
        return self.parent
    
    @tree_parent.setter
    def tree_parent(self, value):
        """ This signature gets overriden by mptt when mptt is used """
        self.parent = value
            
    def get_children(self):
        """ This signature gets overriden by mptt when mptt is used """
        from rapidsms.contrib.locations.models import Location
        return Location.objects.filter(parent_id=self.id, is_active=True).order_by('name')
        
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
        ret = Location.objects.filter(id__in=pks, is_active=True)
        return ret
    
    def get_descendents_plus_self(self):
        # utility to facilitate calling function from django template
        return self.get_descendents(include_self=True)
    
    def peers(self):
        from rapidsms.contrib.locations.models import Location
        # rl: is there a better way to do this?
        if 'mptt' in settings.INSTALLED_APPS:
            return Location.objects.filter(tree_parent=self.tree_parent, is_active=True).order_by('name')
        return Location.objects.filter(parent_id=self.parent_id, is_active=True).order_by('name')
        

    def child_facilities(self):
        from logistics.models import SupplyPoint
        # rl: is there a better way to do this?
        if 'mptt' in settings.INSTALLED_APPS:
            return SupplyPoint.objects.filter(Q(location=self)|Q(location__tree_parent=self), active=True).order_by('name')
        return SupplyPoint.objects.filter(Q(location=self)|Q(location__parent_id=self.pk), active=True).order_by('name')
    
    def facilities(self):
        from logistics.models import SupplyPoint
        return SupplyPoint.objects.filter(location=self, active=True).order_by('name')

    def all_facilities(self):
        from logistics.models import SupplyPoint
        locations = self.get_descendents(include_self=True)
        return SupplyPoint.objects.filter(location__in=locations, active=True).order_by('name')
    
    def all_child_facilities(self):
        from logistics.models import SupplyPoint
        locations = self.get_descendents()
        return SupplyPoint.objects.filter(location__in=locations, active=True).order_by('name')
        
    def _cache_key(self, key, product, producttype, datetime=None):
        return ("LOC-%(location)s-%(key)s-%(product)s-%(producttype)s-%(datetime)s" % \
                {"key": key, "location": self.code, "product": product, 
                 "producttype": producttype, "datetime": datetime}).replace(" ", "-")
    
    def _get_stock_count(self, name, product, producttype):
        """ 
        pulls requested value from cache. refresh cache if necessary
        """
        return self._get_stock_count_for_facilities(self.all_facilities(), name, product, producttype)
    
    """ The following methods express AGGREGATE counts, of all subsumed facilities"""
    def stockout_count(self, product=None, producttype=None):
        return self._get_stock_count("stockout_count", product, producttype)

    def emergency_stock_count(self, product=None, producttype=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        return self._get_stock_count("emergency_stock_count", product, producttype)

    def low_stock_count(self, product=None, producttype=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        return self._get_stock_count("low_stock_count", product, producttype)

    def emergency_plus_low(self, product=None, producttype=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        return self._get_stock_count("emergency_plus_low", product, producttype)

    def good_supply_count(self, product=None, producttype=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        return self._get_stock_count("good_supply_count", product, producttype)

    def overstocked_count(self, product=None, producttype=None):
        return self._get_stock_count("overstocked_count", product, producttype)

    def consumption(self, product=None, producttype=None):
        return self._get_stock_count("consumption", product, producttype)

    def deprecate(self, new_code=None):
        """
        Deprecates a location, by changing the code and deactivating it.
        """
        if new_code is None:
            new_code = "deprecated-%s-%s" % (self.code, uuid.uuid4()) 
        self.code = new_code
        self.is_active = False
        self.save()
