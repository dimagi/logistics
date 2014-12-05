from __future__ import absolute_import
from datetime import datetime
from django.db import models
from logistics.util import config

class Contact(models.Model):
    family_name  = models.CharField(max_length=100, blank=True, verbose_name="Family Name")
    date_updated = models.DateTimeField(blank=True, auto_now_add=True, default=datetime.now())

    def save(self, force_insert=False, force_update=False, using=None):
        self.date_updated = datetime.now()
        super(Contact, self).save(force_insert, force_update, using)

    class Meta:
        abstract = True
        
    def is_incharge(self):
        supervise_resp = config.Responsibilities.REPORTEE_RESPONSIBILITY
        if self.role.responsibilities.filter(code=supervise_resp):
            return True
        return False
