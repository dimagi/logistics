import logging
from dateutil.rrule import *
from django.db import models
from django.db.models import Q
from logistics.apps.logistics.models import SupplyPoint
from rapidsms.models import ExtensibleModelBase
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact, Connection
from django.contrib.auth.models import User
from rapidsms.contrib.messagelog.models import Message
from datetime import datetime, timedelta
from utils import *
from django.contrib.contenttypes.models import ContentType
from dateutil.relativedelta import relativedelta
from django.db.models import Max
from re import match
from django.utils.translation import ugettext as _
from djtables.cell import Cell
from djtables.column import Column, DateColumn


class SupplyPointStatusType(models.Model):
    """
    This is the status for both R&R process and delivery - could be given a process name field to clarify between the two.
    """
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Facility Status Type"

    def __unicode__(self):
        return self.name

class SupplyPointStatus(models.Model):
    status_type = models.ForeignKey(SupplyPointStatusType)
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
