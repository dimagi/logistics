#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from __future__ import unicode_literals
from rapidsms.apps.base import AppBase
from rapidsms.messages import IncomingMessage, OutgoingMessage
from logistics_project.utils.parsing import string_to_datetime
from datetime import datetime

class App(AppBase):
    """
    Provides an ajax endpoint for accepting quasi-fake incoming messages.
    Useful for data migrations.
    """
    MESSAGE_DATES = {}
    
    # this is largely based on the message tester
    def start(self):
        try:
            self.backend

        except KeyError:
            self.error(
                "To use the migration app, you must add a migration " +\
                "backend named 'migration' to your INSTALLED_BACKENDS")

    
    def parse(self, msg):
        # if this came through the migration backend and has a date
        # set, add a timestamp property, otherwise keep it to utcnow
        # handlers should check this property to override timestamps
        # in all the models if they want to support migration
        if hasattr(msg, "received_at") and msg.received_at \
        and msg.connection.backend.name == "migration":
            msg.timestamp = msg.received_at
        else:
            msg.timestamp = datetime.utcnow()
    
    def cleanup(self, msg):
        """
        Find the logger messages and update the timestamps accordingly
        """
        if msg.connection.backend.name == "migration" \
        and hasattr(msg, "logger_msg"):
            msg.logger_msg.date = msg.timestamp
            msg.logger_msg.save()
        if msg.responses:
            for resp in msg.responses:
                self.MESSAGE_DATES[resp] = msg.timestamp
    
    def outgoing(self, msg): 
        if msg.connection.backend.name == "migration" \
        and msg in self.MESSAGE_DATES and hasattr(msg, "logger_msg"):
            msg.logger_msg.date = self.MESSAGE_DATES.pop(msg)
            msg.logger_msg.save()
        
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
