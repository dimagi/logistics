from django.db import models


class Organization(models.Model):
    """
    An organization. Used for reporting purposes. For now contacts  	
    may belong to at most 1 organization.
    """
    name = models.CharField(max_length=128)
    managed_supply_points = models.ManyToManyField("logistics.SupplyPoint", 
                                                   null=True, blank=True)

    def __unicode__(self):
        return self.name

from .warehouse.models import *
from .signals import *