from datetime import datetime

from django.db import models

from logistics.models import SupplyPoint, Product
from logistics_project.apps.tanzania.models import SupplyPointStatusTypes


class ReportingModel(models.Model):
    organization = models.ForeignKey(SupplyPoint) # viewing organization
    date = models.DateTimeField() # viewing time period

    create_date = models.DateTimeField(editable=False)
    update_date = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        if not self.id:
            self.create_date = datetime.utcnow()
        self.update_date = datetime.utcnow()
        super(ReportingModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class OrganizationSummary(ReportingModel):
    total_orgs = models.PositiveIntegerField(default=0) # 176
    average_lead_time_in_days = models.FloatField(default=0) # 28

    def __unicode__(self):
        return "%s: %s/%s" % (self.organization, self.date.month, self.date.year)
    
class GroupSummary(models.Model):
    """
    Warehouse data related to a particular category of reporting 
    (e.g. stock on hand summary)
    """
    org_summary = models.ForeignKey('OrganizationSummary')
    title = models.CharField(max_length=50, blank=True, null=True) # SOH
    total = models.PositiveIntegerField(default=0)
    responded = models.PositiveIntegerField(default=0)
    on_time = models.PositiveIntegerField(default=0)
    complete = models.PositiveIntegerField(default=0) # "complete" = submitted or responded
    
    @property
    def late(self):
        return self.complete - self.on_time
    
    @property
    def not_responding(self):
        return self.total - self.responded
    
    @property
    def received(self):
        assert self.title in [SupplyPointStatusTypes.DELIVERY_FACILITY,
                              SupplyPointStatusTypes.SUPERVISION_FACILITY]
        return self.complete
    
    @property
    def not_received(self):
        assert self.title in [SupplyPointStatusTypes.DELIVERY_FACILITY,
                              SupplyPointStatusTypes.SUPERVISION_FACILITY]
        return self.responded - self.complete
    
    @property
    def sup_received(self):
        assert self.title in SupplyPointStatusTypes.SUPERVISION_FACILITY
        return self.complete
    
    @property
    def sup_not_received(self):
        assert self.title == SupplyPointStatusTypes.SUPERVISION_FACILITY
        return self.responded - self.complete
    
    @property
    def del_received(self):
        assert self.title == SupplyPointStatusTypes.DELIVERY_FACILITY
        return self.complete
    
    @property
    def del_not_received(self):
        assert self.title == SupplyPointStatusTypes.DELIVERY_FACILITY
        return self.responded - self.complete
    
    @property
    def not_submitted(self):
        assert self.title in [SupplyPointStatusTypes.SOH_FACILITY,
                              SupplyPointStatusTypes.R_AND_R_FACILITY]
        return self.responded - self.complete
    
    def __unicode__(self):
        return "%s - %s" % (self.org_summary, self.title)
    

class ProductAvailabilityData(ReportingModel):
    product = models.ForeignKey(Product)
    total = models.PositiveIntegerField(default=0)
    with_stock = models.PositiveIntegerField(default=0)
    without_stock = models.PositiveIntegerField(default=0)
    without_data = models.PositiveIntegerField(default=0)

class ProductAvailabilityDashboardChart(object):
    label_color = { "Stocked out" : "#a30808",
                    "Not Stocked out" : "#7aaa7a",
                    "No Stock Data" : "#efde7f"
                  }
    width = 900
    height = 300
    div = "product_availability_summary_plot_placeholder"
    legenddiv = "product_availability_summary_legend"
    xaxistitle = "Products"
    yaxistitle = "Facilities"    

class Alert(ReportingModel):
    text = models.TextField()
    url = models.CharField(max_length=100, blank=True, null=True)
    expires = models.DateTimeField()

class ReportRun(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    complete = models.BooleanField(default=False)
    has_error = models.BooleanField(default=False)


