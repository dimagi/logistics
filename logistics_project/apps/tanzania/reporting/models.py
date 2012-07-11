from datetime import datetime

from django.db import models

from logistics.models import SupplyPoint, Product


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
    historical_responses = models.FloatField(default=0) # 43
    no_responses = models.FloatField(default=0) # 32
    
    def __unicode__(self):
        return "%s - %s" % (self.org_summary, self.title)
    

class GroupData(models.Model):
    """
    Warehouse data related to how a particular category of reporting 
    (e.g. stock on hand) was filled in (e.g. responded, not responded)
    """
    group_summary = models.ForeignKey('GroupSummary')
    group_code = models.CharField(max_length=2, blank=True, null=True) # A
    label = models.CharField(max_length=50, blank=True, null=True) # on_time
    number = models.FloatField(default=0) # 45
    complete = models.BooleanField(default=False) # True
    on_time = models.BooleanField(default=False) # True
    
    def __unicode__(self):
        return "%s:%s" % (self.group_summary, self.label)
    

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
    yaxistitle = "Number"    

class Alert(ReportingModel):
    text = models.TextField()
    url = models.CharField(max_length=100, blank=True, null=True)
    expires = models.DateTimeField()

class ReportRun(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    complete = models.BooleanField(default=False)
    has_error = models.BooleanField(default=False)


