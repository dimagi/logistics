#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms
from apps.httptester.models import Message
import datetime

class App(rapidsms.app.App):
    def handle(self, message):
        self.debug("got message %s" % (message))
        
    def outgoing(self, message):
        django_msg = Message(phone_number=message.connection.identity, body=message.text, date=datetime.datetime.now(), outgoing=True)
        django_msg.save()
        