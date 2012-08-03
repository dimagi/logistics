from django.db import models
from logistics.warehouse_models import ReportingModel
from logistics_project.apps.malawi.util import fmt_pct

class MalawiWarehouseModel(ReportingModel):
    
    class Meta:
        abstract = True
        app_label = "malawi"

class ProductAvailabilityData(MalawiWarehouseModel):
    """
    This will be used to generate the "current stock status" table,
    as well as anything that needs to compute percent with / without 
    stock, oversupplied, undersupplied, etc.
    """
    # NOTE/DRAGONS: there's some hard-coded stuff that depends on this list 
    # matching up with fields below, and in the summary model. Be careful
    # changing property names.
    STOCK_CATEGORIES = ['with_stock', 'under_stock', 'good_stock',
                        'over_stock', 'without_stock', 'without_data']
    
    # Dashboard: current stock status
    # Resupply Qts: % with stockout
    # Stock status: all
    product = models.ForeignKey('logistics.Product')
    total = models.PositiveIntegerField(default=0)
    managed = models.PositiveIntegerField(default=0)
    
    with_stock = models.PositiveIntegerField(default=0)
    under_stock = models.PositiveIntegerField(default=0)
    good_stock = models.PositiveIntegerField(default=0)
    over_stock = models.PositiveIntegerField(default=0)
    without_stock = models.PositiveIntegerField(default=0)
    without_data = models.PositiveIntegerField(default=0)
    
    # unfortunately, we need to separately keep these for the aggregates
    managed_and_with_stock = models.PositiveIntegerField(default=0)
    managed_and_under_stock = models.PositiveIntegerField(default=0)
    managed_and_good_stock = models.PositiveIntegerField(default=0)
    managed_and_over_stock = models.PositiveIntegerField(default=0)
    managed_and_without_stock = models.PositiveIntegerField(default=0)
    managed_and_without_data = models.PositiveIntegerField(default=0)
    
    def set_managed_attributes(self):
        if self.managed:
            for f in ProductAvailabilityData.STOCK_CATEGORIES:
                setattr(self, 'managed_and_%s' % f, getattr(self, f))
        else: 
            for f in ProductAvailabilityData.STOCK_CATEGORIES:
                setattr(self, 'managed_and_%s' % f, 0)                
                            
class ProductAvailabilityDataSummary(MalawiWarehouseModel):
    """
    Aggregates the product availability up to the supply point level,
    no longer dealing with individual products, but just whether anything
    is managed and anything managed falls into the various categories.
    """
    # Sidebar: % with stockout
    # Dashboard: % with stockout
    # Stock status: district/facility breakdowns
    total = models.PositiveIntegerField(default=0)
    any_managed = models.PositiveIntegerField(default=0)
    any_without_stock = models.PositiveIntegerField(default=0)
    any_with_stock = models.PositiveIntegerField(default=0)
    any_under_stock = models.PositiveIntegerField(default=0)
    any_over_stock = models.PositiveIntegerField(default=0)
    any_good_stock = models.PositiveIntegerField(default=0)
    any_without_data = models.PositiveIntegerField(default=0)
    

class ReportingRate(MalawiWarehouseModel):
    """
    Records information used to calculate the reporting rates
    """
    # Dashboard: Reporting Rates
    # Reporting Rates: all
    total = models.PositiveIntegerField(default=0)
    reported = models.PositiveIntegerField(default=0)
    on_time = models.PositiveIntegerField(default=0)
    complete = models.PositiveIntegerField(default=0)
    
    @property
    def late(self): 
        return self.reported - self.on_time
    
    @property
    def missing(self): 
        return self.total - self.reported
    
    # report helpers
    @property
    def pct_reported(self): return fmt_pct(self.reported, self.total)
    
    @property
    def pct_on_time(self):  return fmt_pct(self.on_time, self.total)
    
    @property
    def pct_late(self):     return fmt_pct(self.late, self.total)
    
    @property
    def pct_missing(self):  return fmt_pct(self.missing, self.total)
    
    @property
    def pct_complete(self): return fmt_pct(self.complete, self.total)
        
            
class TimeTracker(MalawiWarehouseModel):
    """
    For keeping track of a time between two events. Currently used for 
    lead times. We keep the number of data points around so that we can
    include multiple values into an average.
    """
    # Lead times: all 
    type = models.CharField(max_length=10) # e.g. ord-ready
    total = models.PositiveIntegerField(default=0) # number of contributions to this
    time_in_seconds = models.PositiveIntegerField(default=0)
    
class OrderRequest(MalawiWarehouseModel):
    """
    Each time an order is made, used to count both regular and emergency
    orders for a particular month.
    """
    # Emergency Orders: all
    product = models.ForeignKey('logistics.Product')
    total = models.PositiveIntegerField(default=0)
    emergency = models.PositiveIntegerField(default=0)
    
class OrderFulfillment(MalawiWarehouseModel):
    """
    Each time an order is fulfilled, add up the amount requested and
    the amount received so we can determine order fill rates.
    """
    # Order Fill Rates: all 
    product = models.ForeignKey('logistics.Product')
    total = models.PositiveIntegerField(default=0)
    quantity_requested = models.PositiveIntegerField(default=0)
    quantity_received = models.PositiveIntegerField(default=0)

class UserProfileData(models.Model):
    supply_point = models.ForeignKey('logistics.SupplyPoint') # name, code, location.point.lat/long
    facility_children = models.PositiveIntegerField(default=0)
    hsa_children = models.PositiveIntegerField(default=0)
    hsa_supervisors = models.PositiveIntegerField(default=0)
    contacts = models.PositiveIntegerField(default=0)
    supervisor_contacts = models.PositiveIntegerField(default=0)
    in_charge = models.PositiveIntegerField(default=0)
    contact_info = models.CharField(max_length=50, null=True, blank=True)
    products_managed = models.TextField()
    last_message = models.ForeignKey('messagelog.Message', null=True)

    class Meta:
        app_label = "malawi"

# Other:
# HSA (no changes needed)
# Consumption Profiles (likely changes needed, to be clarified)
# Resupply Qts: anything needed? TBD
# Alerts: TBD
