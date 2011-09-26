#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from rapidsms.apps.base import AppBase
from rapidsms.models import Contact

class App(AppBase):
    def start (self):
        """Configure your app in the start phase."""
        pass

    def parse (self, message):
        """Parse and annotate messages in the parse phase."""
        try:
            logistics_contact = Contact.objects.get(connection=message.connection)
        except Contact.DoesNotExist:
            # user is not registered. that's fine, just pass.
            return
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
