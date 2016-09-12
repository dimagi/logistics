from __future__ import absolute_import
from django.db import models
from django.db.models.fields.related import ForeignKey
from django.utils.translation.trans_real import translation
from rapidsms.conf import settings as rapidsms_settings


class MalawiContactExtension(models.Model):
    
    organization = ForeignKey('malawi.Organization', null=True, blank=True)
    
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

    def translate(self, message):
        """
        In newer versions of Django, this is accomplished using the
        django.utils.translation.override context manager.

        We could write our own context manager, but this process mirrors
        the one used in rapidsms.messages.outgoing.
        """
        language = self.language or rapidsms_settings.LANGUAGE_CODE
        return translation(language).gettext(message)
