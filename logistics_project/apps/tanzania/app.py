#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.apps.base import AppBase
from datetime import datetime

class App(AppBase):
    """
    Rapidsms likes you to have this file 
    """
    
    def parse(self, msg):
        # if this came through the migration backend and has a date
        # set, add a timestamp property, otherwise keep it to utcnow
        # tz handlers should check this property to override timestamps
        # in all the models
        if hasattr(msg, "received_at") and msg.received_at \
           and msg.connection.backend.name == "migration":
            msg.timestamp = msg.received_at
        else:
            msg.timestamp = datetime.utcnow()
    