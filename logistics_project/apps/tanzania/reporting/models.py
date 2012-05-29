from datetime import datetime

from django.db import models

from logistics.models import SupplyPoint, Product


############### FOR REPORTS ###################
###### Blow these away and rerun reports ######
###############################################

class ReportingModel(models.Model):
    organization = models.ForeignKey(SupplyPoint)
    date = models.DateTimeField()
    create_date = models.DateTimeField(editable=False, auto_now_add=True)
    update_date = models.DateTimeField(editable=False, auto_now=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.create_date = datetime.utcnow()
        self.update_date = datetime.utcnow()
        super(ReportingModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True

class DistrictSummary(ReportingModel):
    total_facilities = models.PositiveIntegerField(default=0)
    submit_group = models.TextField()
    processing_group = models.TextField()
    delivery_group = models.TextField()
    group_a_complete = models.PositiveIntegerField(default=0)
    group_a_total = models.PositiveIntegerField(default=0)
    group_b_complete = models.PositiveIntegerField(default=0)
    group_b_total = models.PositiveIntegerField(default=0)  
    group_c_complete = models.PositiveIntegerField(default=0)
    group_c_total = models.PositiveIntegerField(default=0)
    average_lead_time_in_days = models.FloatField(default=0)

class ProductAvailabilitySummary(ReportingModel):
    data = models.TextField()
    width = models.PositiveIntegerField(default=900)
    height = models.PositiveIntegerField(default=300)
    div = models.TextField()
    legenddiv = models.TextField()
    flot_data = models.TextField()
    xaxistitle = models.TextField()
    yaxistitle = models.TextField()
    max_value = models.PositiveIntegerField(default=0)

# class ProductAvailabilitySummary(models.Model):
#     product = models.ForeignKey(Product)
#     stocked_out = models.PositiveIntegerField(default=0)
#     not_stocked_out = models.PositiveIntegerField(default=0)
#     no_data = models.PositiveIntegerField(default=0)

class PieCharts(ReportingModel):
    soh_title = models.TextField()
    soh_json = models.TextField()
    randr_title = models.TextField()
    randr_json = models.TextField()
    supervision_title = models.TextField()
    supervision_json = models.TextField()
    delivery_title = models.TextField()
    delivery_json = models.TextField()

# # this might be better
# class PieChartType(ReportingModel):
#     name = models.TextField()
# 
# # https://github.com/derek-schaefer/django-json-field
# from json_field import JSONField
# class PieChart(ReportingModel):
#     title = models.TextField()
#     data = models.JSONField()
#     type = models.ForeignKey('PieChartType')


class SOHPie(ReportingModel):
    on_time = models.PositiveIntegerField(default=0)
    late = models.PositiveIntegerField(default=0)
    not_responding = models.PositiveIntegerField(default=0)

class RRPie(ReportingModel):
    on_time = models.PositiveIntegerField(default=0)
    late = models.PositiveIntegerField(default=0)
    not_submitted = models.PositiveIntegerField(default=0)
    not_responding = models.PositiveIntegerField(default=0)
    historical_response_rate = models.FloatField(default=0)

class SupervisionPie(ReportingModel):
    received = models.PositiveIntegerField(default=0)
    not_received = models.PositiveIntegerField(default=0)
    not_responding = models.PositiveIntegerField(default=0)
    historical_response_rate = models.FloatField(default=0)

class DeliveryPie(ReportingModel):
    received = models.PositiveIntegerField(default=0)
    not_received = models.PositiveIntegerField(default=0)
    not_responding = models.PositiveIntegerField(default=0)
    average_lead_time_in_days = models.FloatField(default=0)


