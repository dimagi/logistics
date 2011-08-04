from django.db import models
from logistics.apps.logistics.models import SupplyPoint
from logistics.apps.logistics.util import config

class SupplyPointStatusTypes(object):
    DELIVERY_RECEIVED_FACILITY = "del_rec_fac"
    DELIVERY_QUANTITIES_REPORTED = "del_quant_rep"
    R_AND_R_SUBMITTED_DISTRICT_TO_MSD = "rr_sub_dist_msd"
    R_AND_R_SUBMITTED_FACILITY_TO_DISTRICT = "rr_sub_fac_dist"
    R_AND_R_REMINDER_SENT_TO_FACILITY = "rr_rem_sent_fac"
    R_AND_R_REMINDER_SENT_TO_DISTRICT = "rr_rem_sent_dist"
    DELIVERY_RECEIVED_REMINDER_SENT_TO_FACILITY = "del_rec_rem_sent_fac"
    R_AND_R_NOT_SUBMITTED_FACILITY_TO_DISTRICT =  "rr_not_sub_fac_dist"
    DELIVERY_NOT_RECEIVED_FACILITY = "del_not_rec_fac"
    SOH_REMINDER_SENT_FACILITY = "soh_rem_sent_fac"
    DELIVERY_RECEIVED_DISTRICT = "del_rec_dist"
    DELIVERY_NOT_RECEIVED_DISTRICT = "del_not_rec_dist"
    DELIVERY_RECEIVED_REMINDER_SENT_DISTRICT = "del_rec_rem_sent_dist"
    SUPERVISION_REMINDER_SENT_FACILITY = "sup_rem_sent_fac"
    SUPERVISION_RECEIVED_FACILITY = "sup_rec_fac"
    SUPERVISION_NOT_RECEIVED_FACILITY = "sup_not_rec_fac"
    LOST_ADJUSTED_REMINDER_SENT_TO_FACILITY = "la_rem_sent_fac"
    ALERT_DELINQUENT_DELIVERY_SENT_TO_FACILITY = "del_del_sent_fac"
    
    CHOICES = (
        (DELIVERY_RECEIVED_FACILITY, "Delivery received"),
        (DELIVERY_QUANTITIES_REPORTED, "Delivery quantities reported"),
        (R_AND_R_SUBMITTED_DISTRICT_TO_MSD, "R&R Submitted from District to MSD"),
        (R_AND_R_SUBMITTED_FACILITY_TO_DISTRICT, "R&R Submitted From Facility to District"),
        (R_AND_R_REMINDER_SENT_TO_FACILITY, "Waiting R&R sent confirmation"),
        (R_AND_R_REMINDER_SENT_TO_DISTRICT, "R&R Reminder Sent to District"),
        (DELIVERY_RECEIVED_REMINDER_SENT_TO_FACILITY, "Waiting Delivery Confirmation"),
        (R_AND_R_NOT_SUBMITTED_FACILITY_TO_DISTRICT,  "R&R Not Submitted"),
        (DELIVERY_NOT_RECEIVED_FACILITY, "Delivery Not Received"),
        (SOH_REMINDER_SENT_FACILITY, "Stock on hand reminder sent to Facility"),
        (DELIVERY_RECEIVED_DISTRICT, "Delivery received"),
        (DELIVERY_NOT_RECEIVED_DISTRICT, "Delivery not received"),
        (DELIVERY_RECEIVED_REMINDER_SENT_DISTRICT, "Waiting Delivery Confirmation"),
        (SUPERVISION_REMINDER_SENT_FACILITY, "Supervision Reminder Sent"),
        (SUPERVISION_RECEIVED_FACILITY, "Supervision Received"),
        (SUPERVISION_NOT_RECEIVED_FACILITY, "Supervision Not Received"),
        (LOST_ADJUSTED_REMINDER_SENT_TO_FACILITY, "Lost/Adjusted Reminder sent to Facility"),
        (ALERT_DELINQUENT_DELIVERY_SENT_TO_FACILITY, "Delinquent deliveries summary sent to District")
    )

    def get_display_name(self, slug):
        return dict(self.CHOICES)[slug]

class SupplyPointStatus(models.Model):
    status_type = models.CharField(choices=SupplyPointStatusTypes.CHOICES, 
                                   max_length=50)
    #message = models.ForeignKey(Message)
    status_date = models.DateTimeField()
    supply_point = models.ForeignKey(SupplyPoint)

    def status_type_name(self):
        return self.status_type.name

    def supply_point_name(self):
        return self.supply_point.name
    
    def __unicode__(self):
        return self.status_type.name

    class Meta:
        verbose_name = "Facility Status"
        verbose_name_plural = "Facility Statuses"
        get_latest_by = "status_date"
        ordering = ('-status_date',)
