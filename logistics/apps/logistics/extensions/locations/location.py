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
        productstock = ProductStock.objects.get(location=self, product=product)
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
        reporters = Contact.objects.filter(role__responsibilities__slug=REPORTEE_RESPONSIBILITY).distinct()
        return reporters

    def supervisor_report(self, stock_report):
        reportees = self.reportees()
        stockouts = stock_report.stockouts()
        if stockouts:
            for reportee in reportees:
                reportee.message(_('Dear %(name), %(facility)s has reported stockouts of %(stockouts)s') %
                                  {'name': reportee.name,
                                   'facility': reportee.location.name,
                                   'stockouts':stockouts
                                  })
            # only report low supply if there are no stockouts
            return
        low_supply = stock_report.low_supply()
        print unicode(low_supply)
        print "low supply %s" % low_supply
        if low_supply:
            for reportee in reportees:
                reportee.message(_('Dear %(name), %(facility)s has reached reorder levels for %(low_supply)s') %
                                 {'name': reportee.name,
                                  'facility':reportee.location.name,
                                  'low_supply':low_supply})
            # only report over supply if there are no low supplies
            return
        over_supply = stock_report.over_supply()
        if over_supply:
            for reportee in reportees:
                reportee.message(_('Dear %(name), %(facility)s has reported an overstock for %(over_supply)s') %
                                 {'name': reportee.name,
                                   'facility':reportee.location.name,
                                  'over_supply':over_supply})
