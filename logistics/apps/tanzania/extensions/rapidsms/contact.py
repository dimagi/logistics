from __future__ import absolute_import
from django.contrib.auth.models import User
from django.db import models

class TanzaniaContactExtension(models.Model):

    user = models.OneToOneField(User, null=True, blank=True)
    email = models.EmailField(blank=True)
    
    class Meta:
        abstract = True

    def allowed_to_edit(self, current_sdp):
        parent_service_delivery_points_ids = []
        while current_sdp is not None:
            parent_service_delivery_points_ids.append(current_sdp.id)
            current_sdp = current_sdp.parent
        return self.supply_point.id in parent_service_delivery_points_ids

    def is_mohsw_level(self):
        return self.role.name in ["MOHSW", "MSD"]

    def phone(self):
        if self.default_connection:
            return self.default_connection.identity
        else:
            return " "

    def role_name(self):
        return self.role.name

    def supply_point_name(self):
        return self.supply_point.name

    def __unicode__(self):
        return self.name
