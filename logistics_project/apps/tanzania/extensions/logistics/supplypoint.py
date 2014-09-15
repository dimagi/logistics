from __future__ import absolute_import
from django.db import models


class TanzaniaSupplyPointExtension(models.Model):
    is_pilot = models.BooleanField(default=False)
    closest_supply_points = models.ManyToManyField('self', related_name='closest', symmetrical=True,
                                                    limit_choices_to={'is_pilot': True}, null=False, blank=True)

    class Meta:
        abstract = True