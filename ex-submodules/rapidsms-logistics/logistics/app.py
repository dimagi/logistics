#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.apps.base import AppBase
from rapidsms.contrib.scheduler.models import EventSchedule

class App(AppBase):
    bootstrapped = False

    def start (self):
        """Configure your app in the start phase."""
        """Configure your app in the start phase."""
        if not self.bootstrapped:
            self.boostrapped = True

            # set up first soh reminder
            try:
                EventSchedule.objects.get(callback="logistics.apps.logistics.callbacks.first_soh_reminder")
            except EventSchedule.DoesNotExist:
                # 2:15 pm on Thursdays
                schedule = EventSchedule(callback="logistics.apps.logistics.callbacks.first_soh_reminder", \
                                         days_of_week=set([3]), hours=set([14]), minutes=set([15]) )
                schedule.save()

            # set up second soh reminder
            try:
                EventSchedule.objects.get(callback="logistics.apps.logistics.callbacks.second_soh_reminder")
            except EventSchedule.DoesNotExist:
                # 2:15 pm on Mondays
                schedule = EventSchedule(callback="logistics.apps.logistics.callbacks.second_soh_reminder", \
                                         days_of_week=set([0]), hours=set([14]), minutes=set([15]) )
                schedule.save()

    def parse (self, message):
        """Parse and annotate messages in the parse phase."""
        pass

    def handle (self, message):
        """Add your main application logic in the handle phase."""
        pass

    def cleanup (self, message):
        """Perform any clean up after all handlers have run in the
           cleanup phase."""
        pass

    def outgoing (self, message):
        """Handle outgoing message notifications."""
        pass

    def stop (self):
        """Perform global app cleanup when the application is stopped."""
        pass