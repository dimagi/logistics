from __future__ import absolute_import
from django.db import models
from django.db.models import Q

class Location(models.Model):
    """
    Location - the main concept of a location.  Currently covers MOHSW, Regions, Districts and Facilities.
    This could/should be broken out into subclasses.
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        abstract = True

    def children(self):
        from rapidsms.contrib.locations.models import Location
        return Location.objects.filter(parent_id=self.id).order_by('name')

    def facilities(self):
        from logistics.apps.logistics.models import Facility
        # temp hack to get this working for tomorrow's showcase
        # TODO make this properly recursive
        return Facility.objects.filter(location=self).order_by('name')

    def all_facilities(self):
        from logistics.apps.logistics.models import Facility
        # temp hack to get this working for tomorrow's showcase
        # TODO make this properly recursive
        return Facility.objects.filter(Q(location=self)|Q(location__parent_id=self.id)).order_by('name')

    """ The following methods express AGGREGATE counts, of all subsumed facilities"""
    def stockout_count(self, product=None, producttype=None):
        from logistics.apps.logistics.models import stockout_count
        return stockout_count(self.all_facilities, product, producttype)

    def emergency_stock_count(self, product=None, producttype=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        from logistics.apps.logistics.models import emergency_stock_count
        return emergency_stock_count(self.all_facilities, product, producttype)

    def low_stock_count(self, product=None, producttype=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        from logistics.apps.logistics.models import low_stock_count
        return low_stock_count(self.all_facilities, product, producttype)

    def good_supply_count(self, product=None, producttype=None):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        from logistics.apps.logistics.models import good_supply_count
        return good_supply_count(self.all_facilities, product, producttype)

    def overstocked_count(self, product=None, producttype=None):
        from logistics.apps.logistics.models import overstocked_count
        return overstocked_count(self.all_facilities, product, producttype)

    def consumption(self, product=None, producttype=None):
        from logistics.apps.logistics.models import consumption
        return consumption(self.all_facilities, product, producttype)
