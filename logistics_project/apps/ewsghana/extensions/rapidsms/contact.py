from __future__ import absolute_import
from django.db import models
from logistics.util import config

class Contact(models.Model):
    family_name  = models.CharField(max_length=100, blank=True, verbose_name="Family Name")

    class Meta:
        abstract = True
        
    def is_incharge(self):
        supervise_resp = config.Responsibilities.REPORTEE_RESPONSIBILITY
        if self.role.responsibilities.filter(code=supervise_resp):
            return True
        return False
