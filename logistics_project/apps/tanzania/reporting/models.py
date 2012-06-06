from datetime import datetime

from django.db import models

from logistics.models import SupplyPoint, Product


############### FOR REPORTS ###################
###### Blow these away and rerun reports ######
###############################################

class ReportingModel(models.Model):
    organization = models.ForeignKey(SupplyPoint) # viewing organization
    date = models.DateTimeField() # viewing time period

    create_date = models.DateTimeField(editable=False, auto_now_add=True)
    update_date = models.DateTimeField(editable=False, auto_now=True)

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

class GroupSummary(models.Model):
    org_summary = models.ForeignKey('OrganizationSummary')
    title = models.TextField() # SOH
    historical_response_rate = models.FloatField(default=0) # 0.432

class GroupData(models.Model):
    group_summary = models.ForeignKey('GroupSummary')
    group_code = models.CharField(max_length=50, blank=True, null=True) # A
    label = models.TextField() # on_time
    number = models.FloatField(default=0) # 45
    complete = models.BooleanField(default=False) # True

class ProductAvailabilityData(ReportingModel):
    product = models.ForeignKey(Product)
    total = models.PositiveIntegerField(default=0)
    with_stock = models.PositiveIntegerField(default=0)
    without_stock = models.PositiveIntegerField(default=0)
    without_data = models.PositiveIntegerField(default=0)

class ProductAvailabilityDashboardChart(ReportingModel):
    label = models.TextField()
    color = models.TextField()

    width = models.PositiveIntegerField(default=900)
    height = models.PositiveIntegerField(default=300)
    div = models.TextField()
    legenddiv = models.TextField()
    xaxistitle = models.TextField()
    yaxistitle = models.TextField()

class Alert(ReportingModel):
    text = models.TextField()
    url = models.TextField()
    expires = models.DateTimeField()

#########################

# class PieChartType(ReportingModel):
#     name = models.TextField()
# 
# # https://github.com/derek-schaefer/django-json-field
# from json_field import JSONField
# class PieChart(ReportingModel):
#     title = models.TextField()
#     data = models.JSONField()
#     type = models.ForeignKey('PieChartType')

