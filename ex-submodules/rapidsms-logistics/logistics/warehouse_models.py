from __future__ import unicode_literals
from builtins import object
from django.db import models
from datetime import datetime

class HistoricalStockCache(models.Model):
    """
    A simple class to cache historical stock levels by month/year per product/facility
    """        
    supply_point = models.ForeignKey('logistics.SupplyPoint', on_delete=models.CASCADE)
    product = models.ForeignKey('logistics.Product', on_delete=models.CASCADE,  null=True)
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    stock = models.IntegerField(null=True)

class BaseReportingModel(models.Model):
    """
    A model to encapsulate aggregate (data warehouse) data used by a report.
    """
    supply_point = models.ForeignKey('logistics.SupplyPoint', on_delete=models.CASCADE) # viewing supply point
    create_date = models.DateTimeField(editable=False)
    update_date = models.DateTimeField(editable=False)
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.create_date = datetime.utcnow()
        self.update_date = datetime.utcnow()
        super(BaseReportingModel, self).save(*args, **kwargs)
        
    class Meta(object):
        abstract = True


class ReportingModel(BaseReportingModel):
    """
    A model to encapsulate aggregate (data warehouse) data used by a report.
    
    Just a BaseReportingModel + a date.
    """
    date = models.DateTimeField()                   # viewing time period
    
    
    class Meta(object):
        abstract = True

class SupplyPointWarehouseRecord(models.Model):
    """
    When something gets updated in the warehouse, create a record of having
    done that.
    """
    supply_point = models.ForeignKey('logistics.SupplyPoint', on_delete=models.CASCADE)
    create_date = models.DateTimeField()
