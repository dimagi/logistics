from django.db import models
from static.malawi.config import BaseLevel


class MalawiProfileExtension(models.Model):

    organization = models.ForeignKey('malawi.Organization', null=True, blank=True)

    # True if this user can view the HSA-level dashboard and reports
    can_view_hsa_level_data = models.BooleanField(default=True)

    # True if this user can view the facility-level dashboard and reports
    can_view_facility_level_data = models.BooleanField(default=False)

    # One of the base level constants representing the current dashboard the user sees upon login
    current_dashboard_base_level = models.CharField(max_length=1, default=BaseLevel.HSA)

    class Meta:
        abstract = True
