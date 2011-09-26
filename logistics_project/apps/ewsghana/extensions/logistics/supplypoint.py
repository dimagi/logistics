from __future__ import absolute_import
from django.db import models
from django.db.models import Q

class SupplyPoint(models.Model):
    supervised_by = models.ForeignKey("logistics.SupplyPoint", related_name="supervising_facility", null=True, blank=True)

    class Meta:
        abstract = True

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
