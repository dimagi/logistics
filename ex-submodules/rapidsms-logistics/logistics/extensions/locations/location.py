from __future__ import absolute_import
from datetime import datetime, timedelta
from django.db import models
from django.utils.translation import ugettext as _

STOCK_ON_HAND_RESPONSIBILITY = 'reporter'
REPORTEE_RESPONSIBILITY = 'reportee'
SUPERVISOR_RESPONSIBILITY = 'supervisor'

class Location(models.Model):
    """
    Location - the main concept of a location.  Currently covers MOHSW, Regions, Districts and Facilities.
    This could/should be broken out into subclasses.
    """
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=100, blank=True, null=True)
    last_reported = models.DateTimeField(default=None, blank=True, null=True)

    class Meta:
        abstract = True

    @property
    def label(self):
        return unicode(self)

    # We use 'last_reported' above instead of the following to generate reports of lateness and on-timeness.
    # This is faster and more readable, but it's duplicate data in the db, which is bad db design. Fix later?
    #@property
    #def last_reported(self):
    #    from logistics.apps.logistics.models import ProductReport, ProductStock
    #    report_count = ProductReport.objects.filter(location=self).count()
    #    if report_count > 0:
    #        last_report = ProductReport.objects.filter(location=self).order_by("-report_date")[0]
    #        return last_report.report_date
    #    return None

    def report(self, product, report_type, quantity, message=None):
        from logistics.apps.logistics.models import ProductReport, ProductStock
        npr = ProductReport( product=product, report_type=report_type, quantity=quantity, message=message, location=self)
        npr.save()
        try:
            productstock = ProductStock.objects.get(location=self, product=product)
        except ProductStock.DoesNotExist:
            productstock = ProductStock(is_active=False, location=self, product=product)
        productstock.quantity = quantity
        productstock.save()
        self.last_reported = datetime.now()
        self.save()
        return npr

    def reporters(self):
        from logistics.apps.logistics.models import Contact
        reporters = Contact.objects.filter(location=self)
        reporters = Contact.objects.filter(role__responsibilities__slug=STOCK_ON_HAND_RESPONSIBILITY).distinct()
        return reporters

    def reportees(self):
        from logistics.apps.logistics.models import Contact
        reporters = Contact.objects.filter(location=self)
        reporters = reporters.filter(role__responsibilities__slug=REPORTEE_RESPONSIBILITY).distinct()
        return reporters

    def children(self):
        from rapidsms.contrib.locations.models import Location
        return Location.objects.filter(parent_id=self.id)

    def report_to_supervisor(self, report, kwargs):
        reportees = self.reportees()
        for reportee in reportees:
            kwargs['admin_name'] = reportee.name
            reportee.message(report % kwargs)

