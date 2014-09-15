from __future__ import absolute_import
from django.db import models


class TanzaniaSupplyPointExtension(models.Model):
    nearests_supply_points = models.ManyToManyField('self', related_name='nearests', symmetrical=False)

    class Meta:
        abstract = True