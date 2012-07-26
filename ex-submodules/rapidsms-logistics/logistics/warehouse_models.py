from django.db import models
from datetime import datetime

class HistoricalStockCache(models.Model):
    """
    A simple class to cache historical stock levels by month/year per product/facility
    """        
    supply_point = models.ForeignKey('SupplyPoint')
    product = models.ForeignKey('Product', null=True)
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    stock = models.IntegerField(null=True)
    

class ReportingModel(models.Model):
    """
    A model to encapsulate aggregate (data warehouse) data used by a report.
    """
    organization = models.ForeignKey('SupplyPoint') # viewing organization
    date = models.DateTimeField()                   # viewing time period

    create_date = models.DateTimeField(editable=False)
    update_date = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        if not self.id:
            self.create_date = datetime.utcnow()
        self.update_date = datetime.utcnow()
        super(ReportingModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True

class ReportRun(models.Model):
    """
    Log of whenever the warehouse models get updated.
    """
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    complete = models.BooleanField(default=False)
    has_error = models.BooleanField(default=False)

