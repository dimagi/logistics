from __future__ import absolute_import
from django.db import models

class Connection(models.Model):
    to  = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        abstract = True
        unique_together = (('backend', 'identity'),)
