from __future__ import unicode_literals
from django.db import models

class ReportRun(models.Model):
    """
    Log of whenever the warehouse models get updated.
    """
    start = models.DateTimeField() # the start of the period covered (from a data perspective)
    end = models.DateTimeField()   # the end of the period covered (from a data perspective)
    start_run = models.DateTimeField()        # when this started
    end_run = models.DateTimeField(null=True) # when this finished
    complete = models.BooleanField(default=False)
    has_error = models.BooleanField(default=False)

    @classmethod
    def last_success(cls):
        """
        The last successful execution of a report, or None if no records found.
        """
        qs = cls.objects.filter(complete=True, has_error=False)
        return qs.order_by("-start_run")[0] if qs.count() else None

