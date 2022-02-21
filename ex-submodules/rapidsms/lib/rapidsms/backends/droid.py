#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import time
import os

from ..models import Connection
from ..messages.incoming import IncomingMessage
from .base import BackendBase

from ..utils.modules import try_import
android = try_import('android')

DELETE_NEW_MESSAGES_ON_ANDROID = False

class Backend(BackendBase):
    _title = "AndroidBackend"


    # number of seconds to wait between
    # polling the modem for incoming SMS
    POLL_INTERVAL = 10

    # time to wait for the start method to
    # complete before assuming that it failed
    MAX_CONNECT_TIME = 10


    def configure(self, **kwargs):
        if 'AP_PORT' in kwargs:
            os.environ['AP_PORT'] = kwargs['AP_PORT']
        else:
            os.environ['AP_PORT'] = '9999'
            
        if 'SERVER_PORT' in kwargs:
            os.system('adb forward tcp:' + str(os.environ['AP_PORT']) + ' tcp:' + kwargs['SERVER_PORT'])
        else:
            os.system('adb forward tcp:' + str(os.environ['AP_PORT']) + ' tcp:55625') 
            
            
        if android is None:
            raise ImportError(
                "The rapidsms.backends.droid engine is not available, " +
                "because Android script is not installed.")


    def __str__(self):
        return self._title


    def send(self, message):

        # attempt to send the message
        # failure is bad, but not fatal
        
        
        if not self.droid:
            self.droid_log("Android not found!","error")
            return False
        
        ########## FIX THIS #################
        sent_msg = self.droid.smsSend(message.connection.identity,message.text)
        ##############################
        
        if not sent_msg.error: self.sent_messages += 1
        else:        self.failed_messages += 1

        return True


    def droid_log(self, str, level):
        self.debug("%s: %s" % (level, str))


#    def status(self):
#
#        # abort if the modem isn't connected
#        # yet. there's no status to fetch
#        if not self._wait_for_modem():
#            return None
#
#        csq = self.modem.signal_strength()
#
#        # convert the "real" signal
#        # strength into a 0-4 scale
#        if   not csq:   level = 0
#        elif csq >= 30: level = 4
#        elif csq >= 20: level = 3
#        elif csq >= 10: level = 2
#        else:           level = 1
#
#        vars = {
#            "_signal":  level,
#            "_title":   self.title,
#            "Messages Sent": self.sent_messages,
#            "Messages Received": self.received_messages }
#
#        # pygsm can return the name of the network
#        # operator since b19cf3. add it if we can
#        if hasattr(self.modem, "network"):
#            vars["Network Operator"] = self.modem.network
#
#        return vars

    def _next_message(self):
        """
        See if there are new messages and 
        return first received new message (lowest ID first)
        remember to mark mesage as read/delete it
        if the message is returned here.
        else return None
        """
        if not self.droid:
            self.droid_log("Can't find android!","error")
            return None
        
        q = self.droid.smsGetMessages(True,"inbox")
        if not q.result:
            return None
        first_msg = q.result[-1]
        self.droid.smsMarkMessageRead([first_msg["_id"]],True)
        
        
        if DELETE_NEW_MESSAGES_ON_ANDROID:
            #be careful with this on a personal phone!!!
            self.droid.smsDeleteMessage(first_msg["_id"])
        msg = {"sender":first_msg["address"],"text":first_msg["body"]}
        return msg
        
        
        
        return None
    
    def run(self):
        while self.running:
            self.info("Polling modem for messages")
            msg = self._next_message()

            if msg is not None:
                self.received_messages += 1

                # we got an sms! hand it off to the
                # router to be dispatched to the apps
                x = self.message(msg["sender"], msg["text"])
                self.router.incoming_message(x)

            # wait for POLL_INTERVAL seconds before continuing
            # (in a slightly bizarre way, to ensure that we abort
            # as soon as possible when the backend is asked to stop)
            for n in range(0, self.POLL_INTERVAL*10):
                if not self.running: return None
                time.sleep(0.1)

        self.info("Run loop terminated.")


    def start(self):
        try:
            self.sent_messages = 0
            self.failed_messages = 0
            self.received_messages = 0

            self.info("Connecting and booting Android phone...")
            self.droid = android.Android()


            # call the superclass to start the run loop -- it just sets
            # ._running to True and calls run, but let's not duplicate it.
            BackendBase.start(self)

        except:

            raise


    def stop(self):

        # call superclass to stop--sets self._running
        # to False so that the 'run' loop will exit cleanly.
        BackendBase.stop(self)

