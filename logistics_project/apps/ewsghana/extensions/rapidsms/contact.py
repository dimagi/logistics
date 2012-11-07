from __future__ import absolute_import
from django.db import models

class Contact(models.Model):
    family_name  = models.CharField(max_length=100, blank=True, verbose_name="Family Name")

    class Meta:
        abstract = True
