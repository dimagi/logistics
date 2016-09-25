from django.db import models
from logistics.util import config


class MalawiProductTypeExtension(models.Model):
    base_level = models.CharField(max_length=1, default=config.BaseLevel.HSA)

    class Meta:
        abstract = True
