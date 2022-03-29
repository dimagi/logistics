#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from __future__ import unicode_literals
import re
from re import IGNORECASE
from rapidsms.apps.base import AppBase
from rapidsms.models import Contact

class App(AppBase):
    def start (self):
        """Configure your app in the start phase."""
        pass

    def parse (self, message):
        """Parse and annotate messages in the parse phase."""
        import re
        message.text = message.text.strip()
        match = re.match("ews", message.text.strip(), flags=IGNORECASE)
        if match:
            message.text = message.text[match.end(0):].strip()

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
