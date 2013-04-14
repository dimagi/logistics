from __future__ import absolute_import
from django.db import models
from rapidsms.models import Contact
from email_reports.models import ReportSubscription, \
    SchedulableReport, WeeklyReportSubscription
from logistics.models import ProductType
from rapidsms.conf import settings

class LogisticsProfile(models.Model):
    sms_notifications = models.BooleanField(default=False)
    contact = models.OneToOneField(Contact, null=True, blank=True)
    program = models.ForeignKey(ProductType, blank=True, null=True)
    # not used for anything except data collection
    organization = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        abstract = True
        
    def name(self):
        return self.user.first_name if self.user.first_name else self.user.username
    
    def get_or_create_contact(self):
        if self.contact is not None:
            return self.contact
        contact = Contact(name=self.user.username)
        contact.save()
        self.contact = contact
        self.save()
        return self.contact

    def deactivate(self):
        if self.contact:
            self.contact.deactivate()
        self.is_active = False
        self.save()
        
    def is_subscribed_to_email_summary(self):
        if ReportSubscription.objects.filter(report__view_name__contains='summary')\
                                     .filter(users=self).exists():
            return True
        return False

    def subscribe_to_email_summary(self):
        TUESDAY = 1
        NINE_AM = 9
        try:
            summary = SchedulableReport.objects.get(view_name__contains='summary')
        except SchedulableReport.DoesNotExist, SchedulableReport.MultipleObjectsReturned:
            raise
        report = WeeklyReportSubscription()
        report.day_of_week = TUESDAY
        report.hours = NINE_AM
        report.report = summary
        if self.supply_point:
            location_code = self.supply_point.location.code
        elif self.location:
            location_code = self.location.code
        else:
            location_code = settings.COUNTRY
        report.view_args = {'place':location_code}
        report.save()
        report.users.add(self.user)
        report.save()
        
    def unsubscribe_to_email_summary(self):
        subscribed = ReportSubscription.objects.filter(report__view_name__contains='summary')\
                                       .filter(users=self)
        subscribed.delete()
