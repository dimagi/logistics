from django.contrib.auth.models import User
from django.db import models
from datetime import datetime
from logistics.models import SupplyPoint, SupplyPointGroup
from logistics_project.apps.tanzania.tasks import email_report
from rapidsms.contrib.messagelog.models import Message


class DeliveryGroups(object):
    GROUPS = ('A', 'B', 'C')

    def __init__(self, month=None, facs = None):
        self.month = month if month else datetime.utcnow().month
        self.facs = facs
        
    # Current submitting group: Jan = A
    # Current processing group: Jan = C
    # Current delivering group: Jan = B

    def current_submitting_group(self, month=None):
        month = month if month else self.month
        return self.GROUPS[(month + 2) % 3]

    def current_processing_group(self, month=None):
        month = month if month else self.month
        return self.current_submitting_group(month=(month+2))

    def current_delivering_group(self, month=None):
        month = month if month else self.month
        return self.current_submitting_group(month=(month+1))

    def delivering(self, facs=None, month=None):
        if not facs: facs = self.facs
        if not facs: return SupplyPoint.objects.none()
        return facs.filter(groups__code=self.current_delivering_group(month))

    def processing(self, facs=None, month=None):
        if not facs: facs = self.facs
        if not facs: return SupplyPoint.objects.none()
        return facs.filter(groups__code=self.current_processing_group(month))

    def submitting(self, facs=None, month=None):
        if not facs: facs = self.facs
        if not facs: return SupplyPoint.objects.none()
        return facs.filter(groups__code=self.current_submitting_group(month))

    def total(self):
        return self.facs.filter(active=True, groups__code__in=self.GROUPS)

    def facilities_by_group(self, month=datetime.utcnow().month):
        groups = {}
        facs = self.facs if self.facs else SupplyPoint.objects.filter(type__code="facility")
        groups['submitting'] = self.submitting(facs, month)
        groups['processing'] = self.processing(facs, month)
        groups['delivering'] = self.delivering(facs, month)
        groups['total'] = list(facs)
        return groups

class OnTimeStates(object):
    ON_TIME = "on time"
    LATE = "late"
    NO_DATA = "no data"
    INSUFFICIENT_DATA = "insufficient data"

class SupplyPointStatusValues(object):
    RECEIVED = "received"
    NOT_RECEIVED = "not_received"
    SUBMITTED = "submitted"
    NOT_SUBMITTED = "not_submitted"
    REMINDER_SENT = "reminder_sent"
    ALERT_SENT = "alert_sent"
    CHOICES = [RECEIVED, NOT_RECEIVED, SUBMITTED,
               NOT_SUBMITTED, REMINDER_SENT, ALERT_SENT]
    
class SupplyPointStatusTypes(object):
    DELIVERY_FACILITY = "del_fac"
    DELIVERY_DISTRICT = "del_dist"
    R_AND_R_FACILITY = "rr_fac"
    R_AND_R_DISTRICT = "rr_dist"
    SOH_FACILITY = "soh_fac"
    SUPERVISION_FACILITY = "super_fac"
    LOSS_ADJUSTMENT_FACILITY = "la_fac"
    DELINQUENT_DELIVERIES = "del_del"
    DELIVERY_FACILITY = "del_fac"
    
    CHOICE_MAP = {
        DELIVERY_FACILITY: {SupplyPointStatusValues.REMINDER_SENT: "Waiting Delivery Confirmation",
                            SupplyPointStatusValues.RECEIVED: "Delivery received",
                            SupplyPointStatusValues.NOT_RECEIVED: "Delivery Not Received"},
        DELIVERY_DISTRICT: {SupplyPointStatusValues.REMINDER_SENT: "Waiting Delivery Confirmation",
                           SupplyPointStatusValues.RECEIVED: "Delivery received",
                           SupplyPointStatusValues.NOT_RECEIVED: "Delivery not received"},
        R_AND_R_FACILITY: {SupplyPointStatusValues.REMINDER_SENT: "Waiting R&R sent confirmation",
                           SupplyPointStatusValues.SUBMITTED: "R&R Submitted From Facility to District",
                           SupplyPointStatusValues.NOT_SUBMITTED: "R&R Not Submitted"},
        R_AND_R_DISTRICT: {SupplyPointStatusValues.REMINDER_SENT: "R&R Reminder Sent to District",
                           SupplyPointStatusValues.SUBMITTED: "R&R Submitted from District to MSD"},
        SOH_FACILITY: {SupplyPointStatusValues.REMINDER_SENT: "Stock on hand reminder sent to Facility",
                       SupplyPointStatusValues.SUBMITTED: "Stock on hand Submitted"},
        SUPERVISION_FACILITY: {SupplyPointStatusValues.REMINDER_SENT: "Supervision Reminder Sent",
                               SupplyPointStatusValues.RECEIVED: "Supervision Received",
                               SupplyPointStatusValues.NOT_RECEIVED: "Supervision Not Received"},
        LOSS_ADJUSTMENT_FACILITY: {SupplyPointStatusValues.REMINDER_SENT: "Lost/Adjusted Reminder sent to Facility"},
        DELINQUENT_DELIVERIES: {SupplyPointStatusValues.ALERT_SENT: "Delinquent deliveries summary sent to District"},
    }
    
    @classmethod
    def get_display_name(cls, type, value):
        return cls.CHOICE_MAP[type][value]
    
    @classmethod
    def is_legal_combination(cls, type, value):
        return type in cls.CHOICE_MAP and value in cls.CHOICE_MAP[type]

class SupplyPointStatus(models.Model):
    status_type = models.CharField(choices=((k, k) for k in SupplyPointStatusTypes.CHOICE_MAP.keys()),
                                   max_length=50)
    status_value = models.CharField(max_length=50,
                                    choices=((c, c) for c in SupplyPointStatusValues.CHOICES))
    status_date = models.DateTimeField(default=datetime.utcnow)
    supply_point = models.ForeignKey(SupplyPoint)

    def save(self, *args, **kwargs):
        if not SupplyPointStatusTypes.is_legal_combination(self.status_type, self.status_value):
            raise ValueError("%s and %s is not a legal value combination" % \
                             (self.status_type, self.status_value))
        super(SupplyPointStatus, self).save(*args, **kwargs)
        
    def __unicode__(self):
        return "%s: %s" % (self.status_type, self.status_value)

    @property
    def name(self):
        return SupplyPointStatusTypes.get_display_name(self.status_type, self.status_value)

    class Meta:
        verbose_name = "Facility Status"
        verbose_name_plural = "Facility Statuses"
        get_latest_by = "status_date"
        ordering = ('-status_date',)
        
class AdHocReport(models.Model):
    supply_point = models.ForeignKey(SupplyPoint)
    recipients = models.TextField(help_text="Use a list of email addresses separated by commas")
    
    def get_recipients(self):
        return [email.strip() for email in self.recipients.split(",")]
    
    def send(self):
        email_report.delay(self.supply_point.code, self.get_recipients())

class SupplyPointNote(models.Model):
    supply_point = models.ForeignKey(SupplyPoint)
    date = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    text = models.TextField()

    def __unicode__(self):
        return "%s at %s on %s: %s" % (self.user.username, self.supply_point.name, self.date, self.text)

class DeliveryGroupReport(models.Model):
    supply_point = models.ForeignKey(SupplyPoint)
    quantity = models.IntegerField()
    report_date = models.DateTimeField(auto_now_add=True, default=datetime.now())
    message = models.ForeignKey(Message)
    delivery_group = models.ForeignKey(SupplyPointGroup)

    class Meta:
        ordering = ('-report_date',)