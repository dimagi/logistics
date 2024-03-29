from __future__ import unicode_literals
import datetime
from rapidsms.apps.base import AppBase
from .models import Message


class App(AppBase):
    def _who(self, msg):
        to_return = {}
        if msg.contact:
            to_return["contact"]    = msg.contact
        if msg.connection:
            to_return["connection"] = msg.connection
        if not to_return:
            raise ValueError
        return to_return

    def _log(self, direction, who, text):
        return Message.objects.create(
            date=datetime.datetime.utcnow(),
            direction=direction,
            text=text,
            **who)

    def parse(self, msg):
        # annotate the message as we log them in case any other apps
        # want a handle to them
        msg.logger_msg = self._log("I", self._who(msg), msg.raw_text)
        if msg.contact:
            msg.contact.last_message = msg.logger_msg
            msg.contact.save()

    def outgoing(self, msg): 
        msg.logger_msg = self._log("O", self._who(msg), msg.text)
