from __future__ import absolute_import
from django.db import models

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
    msd_code = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        abstract = True

    @property
    def label(self):
        return unicode(self)

    def report(self, **kwargs):
        from logistics.apps.logistics.models import ProductReport
        npr = ProductReport(location = self,  **kwargs)
        npr.save()

    def reporters(self):
        from logistics.apps.logistics.models import LogisticsContact
        reporters = LogisticsContact.objects.filter(location=self)
        reporters = LogisticsContact.objects.filter(role__responsibilities__slug=STOCK_ON_HAND_RESPONSIBILITY).distinct()
        return reporters

    def reportees(self):
        from logistics.apps.logistics.models import LogisticsContact
        reporters = LogisticsContact.objects.filter(location=self)
        reporters = LogisticsContact.objects.filter(role__responsibilities__slug=REPORTEE_RESPONSIBILITY).distinct()
        return reporters

    def supervisor_report(self, stock_report):
        sdp = self.parentsdp()
        reportees = sdp.reportees()
        stockouts = stock_report.stockouts()
        if stockouts:
            for reportee in reportees:
                reportee.message(_('%(facility)s is stocked out of %(stockouts)s') %
                                  {'facility': reportee.location.name,
                                   'stockouts':stockouts
                                  })
            # only report low supply if there are no stockouts
            return
        low_supply = stock_report.low_supply()
        if low_supply:
            for reportee in reportees:
                reportee.message(_('%(facility)s is below reorder levels for %(low_supply)s') %
                                 {'facility':reportee.location.name,
                                  'low_supply':low_supply})
            # only report over supply if there are no low supplies
            return
        over_supply = stock_report.over_supply()
        if over_supply:
            for reportee in reportees:
                reportee.message(_('%(facility)s is over maximum stock levels for %(over_supply)s') %
                                 {'facility':reportee.location.name,
                                  'over_supply':over_supply})
