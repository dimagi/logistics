from datetime import datetime
from django.db import models


class Organization(models.Model):
    """
    An organization. Used for reporting purposes. For now contacts  	
    may belong to at most 1 organization.
    """
    name = models.CharField(max_length=128)
    managed_supply_points = models.ManyToManyField("logistics.SupplyPoint", blank=True)

    def __str__(self):
        return self.name


class RefrigeratorMalfunction(models.Model):
    REASON_NO_GAS = '1'
    REASON_POWER_FAILURE = '2'
    REASON_FRIDGE_BREAKDOWN = '3'
    REASON_OTHER = '4'

    REASONS = (
        REASON_NO_GAS,
        REASON_POWER_FAILURE,
        REASON_FRIDGE_BREAKDOWN,
        REASON_OTHER,
    )

    class RefrigeratorNotWorkingException(Exception):
        pass

    # A reference to the facility with the malfunction
    supply_point = models.ForeignKey('logistics.SupplyPoint', on_delete=models.CASCADE,  db_index=True, related_name='+')

    # Contact who reported the malfunction
    reported_by = models.ForeignKey('rapidsms.Contact', on_delete=models.CASCADE,  related_name='+')

    # Timestamp when the facility user reported the malfunction
    reported_on = models.DateTimeField(db_index=True)

    # Takes the value of one of the REASON_* constants above
    malfunction_reason = models.CharField(max_length=1)

    # Timestamp when the district user responded
    responded_on = models.DateTimeField(null=True)

    # Facility where the district user referred the facility user to send their products while the
    # refrigerator was broken
    sent_to = models.ForeignKey('logistics.SupplyPoint', on_delete=models.CASCADE,  null=True, db_index=True, related_name='+')

    # Timestamp when the refrigerator was reported fixed. This is null while broken, not null when fixed.
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
    def new_malfunction(cls, supply_point, malfunction_reason, reported_by):
        cls.objects.create(
            supply_point=supply_point,
            reported_on=datetime.utcnow(),
            reported_by=reported_by,
            malfunction_reason=malfunction_reason,
        )

    @classmethod
    def get_last_reported_malfunction(cls, supply_point):
        result = list(cls.objects.filter(supply_point=supply_point).order_by('-reported_on')[0:1])
        if len(result) == 1:
            return result[0]

        return None


from .warehouse.models import *
from .signals import *
