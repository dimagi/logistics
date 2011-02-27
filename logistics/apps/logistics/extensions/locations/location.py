from __future__ import absolute_import
from django.db import models

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
        return Location.objects.filter(parent_id=self.id)

    def facilities(self):
        from logistics.apps.logistics.models import Facility
        return Facility.objects.filter(location=self)

    """ The following methods express AGGREGATE counts, of all subsumed facilities"""
    def stockout_count(self):
        from logistics.apps.logistics.models import ProductStock
        return ProductStock.objects.filter(facility__in=self.facilities).filter(quantity=0).count()

    def emergency_stock_count(self):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        from logistics.apps.logistics.models import ProductStock
        emergency_stock = 0
        stocks = ProductStock.objects.filter(facility__in=self.facilities).filter(quantity__gt=0)
        for stock in stocks:
            if stock.quantity < stock.emergency_reorder_level:
                emergency_stock = emergency_stock + 1
        return emergency_stock

    def low_stock_count(self):
        """ This indicates all stock below reorder levels,
            including all stock below emergency supply levels
        """
        from logistics.apps.logistics.models import ProductStock
        low_stock_count = 0
        stocks = ProductStock.objects.filter(facility__in=self.facilities).filter(quantity__gt=0)
        for stock in stocks:
            if stock.quantity < stock.reorder_level:
                low_stock_count = low_stock_count + 1
        return low_stock_count

    def overstocked_count(self):
        from logistics.apps.logistics.models import ProductStock
        overstock_count = 0
        stocks = ProductStock.objects.filter(facility__in=self.facilities).filter(quantity__gt=0)
        for stock in stocks:
            if stock.quantity > stock.maximum_level:
                overstock_count = overstock_count + 1
        return overstock_count
