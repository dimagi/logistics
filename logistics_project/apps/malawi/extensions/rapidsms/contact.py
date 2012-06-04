from __future__ import absolute_import
from django.db import models
from django.db.models.fields.related import ForeignKey
from logistics_project.apps.malawi.models import Organization

class MalawiContactExtension(models.Model):
    
    organization = ForeignKey(Organization, null=True, blank=True)
    
    class Meta:
        abstract = True
        
    @property
    def is_hsa(self):
        from logistics.models import ContactRole
        from logistics.util import config
        return self.role == ContactRole.objects.get(code=config.Roles.HSA)
        
    @property
    def associated_supply_point(self):
        """
        For HSA's return the parent facility. For everyone else return the 
        exact supply point.
        """
        from logistics.models import SupplyPoint

        if not self.supply_point: return None

        if self.is_hsa:
            return SupplyPoint.objects.get(location=self.supply_point.location.parent)
        return self.supply_point
    
    @property
    def associated_supply_point_name(self):
        if self.associated_supply_point:
            return self.associated_supply_point.name
        else:
            return ""
    
    @property
    def hsa_id(self):
        if self.is_hsa:
            if self.supply_point:
                return self.supply_point.code
            else:
                return ""
        else:
            return ""