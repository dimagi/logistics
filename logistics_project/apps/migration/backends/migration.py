from __future__ import unicode_literals
from rapidsms.backends.bucket import BucketBackend
from datetime import datetime

class MigrationBackend(BucketBackend):
    """
    Backend to do migrations. Only difference is that its receive method takes
    in a timestamp, to allow you to fake historical messages. 
    
    Your message processing logic must check the appropriate fields of the
    message.
    """
    
    def receive(self, identity, text, timestamp=None):
        msg = self.message(identity, text, timestamp)
        self.router.incoming_message(msg)
        self.bucket.append(msg)
        return msg

    