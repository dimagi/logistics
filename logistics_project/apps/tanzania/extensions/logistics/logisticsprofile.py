from django.db import models


class TanzaniaLogisticsProfileExtension(models.Model):
    date_updated = models.DateTimeField(blank=True, auto_now=True)

    class Meta:
        abstract = True
