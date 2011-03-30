#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib.auth.models import User
from django.db import models
from couchdbkit.ext.django.schema import *
from dimagi.utils.django.email import send_HTML_email
from dimagi.utils.mixins import UnicodeMixIn
from logistics.apps.reports.schedule.config import SCHEDULABLE_REPORTS
from logistics.apps.reports.schedule.html2text import html2text

class ReportNotification(models.Model, UnicodeMixIn):
    report = models.CharField(max_length=100)
    users = models.ManyToManyField(User)
    
    def __unicode__(self):
        return "Notify: %s user(s): %s, report: %s" % \
                (self.__class__.__name__, ",".join([u.username for u in self.users.all()]), self.report)

    def send(self):
        for user in self.users.all():
            report = SCHEDULABLE_REPORTS[self.report]
            body = report.get_response(user)
            send_HTML_email(report.title, user.email, 
                            html2text(body), body)

    
class DailyReportNotification(ReportNotification):
    hours = models.IntegerField()

class WeeklyReportNotification(ReportNotification):
    hours = models.IntegerField()
    day_of_week = models.IntegerField()

