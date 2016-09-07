from datetime import datetime
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


class RefrigeratorMalfunction(models.Model):
    REASON_NO_GAS = '1'
    REASON_POWER_FAILURE = '2'
    REASON_FRIDGE_BREAKDOWN = '3'

    REASONS = (
        REASON_NO_GAS,
        REASON_POWER_FAILURE,
        REASON_FRIDGE_BREAKDOWN,
    )

    # A reference to the facility with the malfunction
    supply_point = models.ForeignKey('logistics.SupplyPoint', db_index=True, related_name='+')

    # Timestamp when the facility user reported the malfunction
    reported_on = models.DateTimeField(db_index=True)

    # Takes the value of one of the REASON_* constants above
    malfunction_reason = models.CharField(max_length=1)

    # Timestamp when the district user responded
    responded_on = models.DateTimeField(null=True)

    # Facility where the district user referred the facility user to
    sent_to = models.ForeignKey('logistics.SupplyPoint', null=True, db_index=True, related_name='+')

    # Timestamp when the refrigerator was fixed. This is null while broken, not null when fixed.
    resolved_on = models.DateTimeField(null=True)

    @classmethod
    def get_open_malfunction(cls, supply_point):
        try:
            return cls.objects.get(
                supply_point=supply_point,
                resolved_on__isnull=True
            )
        except cls.DoesNotExist:
            return None

    @classmethod
    def new_malfunction(cls, supply_point, malfunction_reason):
        cls.objects.create(
            supply_point=supply_point,
            reported_on=datetime.utcnow(),
            malfunction_reason=malfunction_reason,
        )

from .warehouse.models import *
from .signals import *
