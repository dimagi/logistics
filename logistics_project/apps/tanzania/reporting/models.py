from django.db import models

from logistics.models import SupplyPoint, Product


############### FOR REPORTS ###################
###### Blow these away and rerun reports ######
###############################################

class DistrictSummary(models.Model):
    organization = models.ForeignKey(SupplyPoint)
    date = models.DateTimeField()
    total_facilities = models.PositiveIntegerField(default=0)
    group_a_complete = models.PositiveIntegerField(default=0)
    group_a_total = models.PositiveIntegerField(default=0)
    group_b_complete = models.PositiveIntegerField(default=0)
    group_b_total = models.PositiveIntegerField(default=0)  
    group_c_complete = models.PositiveIntegerField(default=0)
    group_c_total = models.PositiveIntegerField(default=0)
    average_lead_time_in_days = models.FloatField(default=0)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

class ProductAvailabilitySummary(models.Model):
    organization = models.ForeignKey(SupplyPoint)
    date = models.DateTimeField()    
    product = models.ForeignKey(Product)
    stocked_out = models.PositiveIntegerField(default=0)
    not_stocked_out = models.PositiveIntegerField(default=0)
    no_data = models.PositiveIntegerField(default=0)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

class SOHPie(models.Model):
    organization = models.ForeignKey(SupplyPoint)
    date = models.DateTimeField()
    on_time = models.PositiveIntegerField(default=0)
    late = models.PositiveIntegerField(default=0)
    not_responding = models.PositiveIntegerField(default=0)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

class RRPie(models.Model):
    organization = models.ForeignKey(SupplyPoint)
    date = models.DateTimeField()
    on_time = models.PositiveIntegerField(default=0)
    late = models.PositiveIntegerField(default=0)
    not_submitted = models.PositiveIntegerField(default=0)
    not_responding = models.PositiveIntegerField(default=0)
    historical_response_rate = models.FloatField(default=0)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

class SupervisionPie(models.Model):
    organization = models.ForeignKey(SupplyPoint)
    date = models.DateTimeField()
    received = models.PositiveIntegerField(default=0)
    not_received = models.PositiveIntegerField(default=0)
    not_responding = models.PositiveIntegerField(default=0)
    historical_response_rate = models.FloatField(default=0)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

class DeliveryPie(models.Model):
    organization = models.ForeignKey(SupplyPoint)
    date = models.DateTimeField()
    received = models.PositiveIntegerField(default=0)
    not_received = models.PositiveIntegerField(default=0)
    not_responding = models.PositiveIntegerField(default=0)
    average_lead_time_in_days = models.FloatField(default=0)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)




