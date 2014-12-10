from __future__ import absolute_import
from datetime import datetime
from django.db import models


class Location(models.Model):
    date_updated = models.DateTimeField(blank=True, auto_now_add=True, default=datetime.now())

    def save(self, force_insert=False, force_update=False, using=None):
        self.date_updated = datetime.now()
        super(Location, self).save(force_insert, force_update, using)

    class Meta:
        abstract = True
