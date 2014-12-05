from __future__ import absolute_import
from itertools import chain
from django.db import models
from logistics.util import config


class SupplyPoint(models.Model):
    supervised_by = models.ForeignKey("logistics.SupplyPoint", 
                                      related_name="supervising_facility", null=True, blank=True)
    primary_reporter = models.ForeignKey("rapidsms.Contact", null=True, 
                                         verbose_name='Primary Stock Reporter', blank=True)

    def save(self, force_insert=False, force_update=False, using=None):
        self.location.save()
        super(SupplyPoint, self).save(force_insert, force_update, using)

    class Meta:
        abstract = True
        ordering = ['name']

    def report_to_supervisor(self, report, kwargs, exclude=None):
        def _report_to_supervisor_at_facility(facility, report, kwargs, exclude):
            if facility is None:
                return
            reportees = facility.reportees()
            if reportees is None:
                return
            if exclude:
                reportees = reportees.exclude(pk__in=[e.pk for e in exclude])
            for reportee in reportees:
                kwargs['admin_name'] = reportee.name
                if reportee.default_connection:
                    reportee.message(report % kwargs)
        _report_to_supervisor_at_facility(self, report, kwargs, exclude)
        _report_to_supervisor_at_facility(self.supervised_by, report, kwargs, exclude)
        
    def add_contact(self, contact):
        # set first reporter to be default primary reporter
        if contact.has_responsibility(config.Responsibilities.STOCK_ON_HAND_RESPONSIBILITY) and \
          self.primary_reporter is None:
            self.primary_reporter = contact
            self.save()

    def deactivate(self):
        self.active = False
        self.save()
        # this is in ewsghana app only because the facility code is deployment-specific
        # if it's a 'real' location, we keep it. if it was only created to track
        # this facility, we deactivate it.
        if not self.location.get_children().exists() and \
          not self.location.facilities().exists() and \
          self.location.type.slug == config.LocationCodes.FACILITY:
            self.location.deactivate()
            
    def incharges(self):
        return list(chain(self.reportees(), 
                          self.supervised_by.reportees() if self.supervised_by else []))