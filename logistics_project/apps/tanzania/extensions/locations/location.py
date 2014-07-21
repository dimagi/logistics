from __future__ import absolute_import
from datetime import datetime
from django.db import models

class TanzaniaLocationExtension(models.Model):
    date_updated = models.DateTimeField(auto_now_add=True)

    def save(self, force_insert=False, force_update=False, using=None):
        self.date_updated = datetime.today()
        super(TanzaniaLocationExtension, self).save(force_insert, force_update, using)

    class Meta:
        abstract = True