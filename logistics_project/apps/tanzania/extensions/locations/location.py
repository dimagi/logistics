from __future__ import absolute_import
from django.db import models

class TanzaniaLocationExtension(models.Model):
    date_updated = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True