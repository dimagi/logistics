""" These models define user's subscriptions to reports specified in schedule/config.py """

#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import json
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from dimagi.utils.django.email import send_HTML_email
from dimagi.utils.mixins import UnicodeMixIn
from logistics.apps.reports.schedule.html2text import html2text
from logistics.apps.reports.schedule.config import SCHEDULABLE_REPORTS

class ReportSubscription(models.Model, UnicodeMixIn):
    report = models.CharField(max_length=100)
    _view_args = models.CharField(max_length=512, null=True, blank=True)
    users = models.ManyToManyField(User)
    
    def __unicode__(self):
        return "Notify: %s user(s): %s, report: %s" % \
                (self.__class__.__name__, ",".join([u.username for u in self.users.all()]), self.report)

    def send(self):
        for user in self.users.all():
            self.send_to_user(user)
    
    def send_to_user(self, user):
        report = SCHEDULABLE_REPORTS[self.report]
        body = report.get_response(user, self.view_args)
        title = report.title
        try:
            name = Site.objects.get().name
            title = "{0} ({1})".format(report.title, name)
        except Site.DoesNotExist:
            pass
        send_HTML_email(title, user.email, 
                        html2text(body), body)

    @property
    def view_args(self):
        if self._view_args:
            return json.loads(self._view_args)
        return self._view_args

    @view_args.setter
    def view_args(self, value):
        self._view_args = json.dumps(value)

    @view_args.deleter
    def view_args(self):
        self._view_args = None

class DailyReportSubscription(ReportSubscription):
    __name__ = "DailyReportNotification"    
    hours = models.IntegerField()

class WeeklyReportSubscription(ReportSubscription):
    __name__ = "WeeklyReportNotification"
    hours = models.IntegerField()
    day_of_week = models.IntegerField()


