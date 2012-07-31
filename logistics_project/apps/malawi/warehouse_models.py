from django.db import models
from logistics.models import Product
from logistics.warehouse_models import ReportingModel


class ProductAvailabilityData(ReportingModel):
    """
    This will be used to generate the "current stock status" table,
    as well as anything that needs to compute percent with / without 
    stock, oversupplied, undersupplied, etc.
    """
    # Sidebar: % with stockout
    # Dashboard: % with stockout, current stock status
    # Resupply Qts: % with stockout
    # Stock status: all
    product = models.ForeignKey(Product)
    total = models.PositiveIntegerField(default=0)
    managed = models.PositiveIntegerField(default=0)
    with_stock = models.PositiveIntegerField(default=0)
    under_stock = models.PositiveIntegerField(default=0)
    over_stock = models.PositiveIntegerField(default=0)
    without_stock = models.PositiveIntegerField(default=0)
    without_data = models.PositiveIntegerField(default=0)
    
    # unfortunately, we need to separately keep these for the aggregates
    managed_and_with_stock = models.PositiveIntegerField(default=0)
    managed_and_under_stock = models.PositiveIntegerField(default=0)
    managed_and_over_stock = models.PositiveIntegerField(default=0)
    managed_and_without_stock = models.PositiveIntegerField(default=0)
    managed_and_without_data = models.PositiveIntegerField(default=0)
    

class ReportingRate(ReportingModel):
    """
    Records information used to calculate the reporting rates
    """
    # Dashboard: Reporting Rates
    # Reporting Rates: all
    total = models.PositiveIntegerField(default=0)
    reported = models.PositiveIntegerField(default=0)
    on_time = models.PositiveIntegerField(default=0)
    complete = models.PositiveIntegerField(default=0)

class TimeTracker(ReportingModel):
    """
    For keeping track of a time between two events. Currently used for 
    lead times. We keep the number of data points around so that we can
    include multiple values into an average.
    """
    # Lead times: all 
    type = models.CharField(max_length=10) # e.g. ord-ready
    total = models.PositiveIntegerField(default=0) # number of contributions to this
    time_in_seconds = models.PositiveIntegerField(default=0)
    
class OrderRequest(ReportingModel):
    """
    Each time an order is made, used to count both regular and emergency
    orders for a particular month.
    """
    # Emergency Orders: all
    product = models.ForeignKey(Product)
    total = models.PositiveIntegerField(default=0)
    emergency = models.PositiveIntegerField(default=0)
    
    
class OrderFulfillment(ReportingModel):
    """
    Each time an order is fulfilled, add up the amount requested and
    the amount received so we can determine order fill rates.
    """
    # Order Fill Rates: all 
    product = models.ForeignKey(Product)
    total = models.PositiveIntegerField(default=0)
    quantity_requested = models.PositiveIntegerField(default=0)
    quantity_received = models.PositiveIntegerField(default=0)

# Other:
# User Profiles (no changes needed)
# HSA (no changes needed)
# Consumption Profiles (likely changes needed, to be clarified)
# Resupply Qts: anything needed? TBD
# Alerts: TBD