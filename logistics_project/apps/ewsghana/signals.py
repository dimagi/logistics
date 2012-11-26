#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from __future__ import absolute_import

from django.db.models.signals import post_save

from alerts.models import NotificationVisibility
from logistics.signals import stockout_resolved, notify_suppliees_of_stockouts_resolved
from logistics.signals import stockout_reported, notify_suppliees_of_stockouts_reported

from .notifications import sms_notifications

stockout_resolved.connect(notify_suppliees_of_stockouts_resolved)
stockout_reported.connect(notify_suppliees_of_stockouts_reported)

post_save.connect(sms_notifications, sender=NotificationVisibility)
