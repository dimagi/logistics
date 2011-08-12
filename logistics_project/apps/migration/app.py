#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import time
from rapidsms.conf import settings
from rapidsms.apps.base import AppBase
from rapidsms.messages import IncomingMessage, OutgoingMessage
from dimagi.utils.parsing import string_to_datetime


class App(AppBase):
    """
    Provides an ajax endpoint for accepting quasi-fake incoming messages.
    Useful for data migrations.
    """
    
    # this is largely based on the message tester
    def start(self):
        try:
            self.backend

        except KeyError:
            self.error(
                "To use the migration app, you must add a migration " +\
                "backend named 'migration' to your INSTALLED_BACKENDS")

    
    @property
    def backend(self):
        return self.router.backends["migration"]


    def ajax_POST_send(self, get, post):
        timestamp = string_to_datetime(post.get("timestamp")) \
                        if "timestamp" in post else None
        msg = self.backend.receive(
            post.get("identity", None),
            post.get("text", ""),
            timestamp)
        return True
    
    def ajax_GET_status(self, get):
        # this method does nothing, but can be used to check if the router 
        # is running
        return ""