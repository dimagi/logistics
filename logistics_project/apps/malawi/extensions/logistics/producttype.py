from django.db import models


class MalawiProductTypeExtension(models.Model):
    is_facility = models.BooleanField(default=False)

    class Meta:
        abstract = True
