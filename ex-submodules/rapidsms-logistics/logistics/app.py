#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.apps.base import AppBase
from rapidsms.contrib.scheduler.models import EventSchedule, set_weekly_event
from logistics.apps.logistics.models import LogisticsContact

class App(AppBase):
    bootstrapped = False

    def start (self):
        """Configure your app in the start phase."""
        if not self.bootstrapped:
            self.bootstrapped = True
            
            # set up first soh reminder
            try:
                EventSchedule.objects.get(callback="logistics.schedule.first_soh_reminder")
            except EventSchedule.DoesNotExist:
                # 2:15 pm on Thursdays
                set_weekly_event("logistics.schedule.first_soh_reminder",3,14,15)

            # set up second soh reminder
            try:
                EventSchedule.objects.get(callback="logistics.schedule.second_soh_reminder")
            except EventSchedule.DoesNotExist:
                # 2:15 pm on Mondays
                set_weekly_event("logistics.schedule.second_soh_reminder",0,14,15)

    def parse (self, message):
        """Parse and annotate messages in the parse phase."""
        try:
            logistics_contact = LogisticsContact.objects.get(connection=message.connection)
        except LogisticsContact.DoesNotExist:
            # user is not registered. that's fine, just pass.
            pass
        message.logistics_contact = logistics_contact

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