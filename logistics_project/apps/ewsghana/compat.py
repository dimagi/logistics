"Compatility layer for different Django or RapidSMS versions."
import datetime

# Forward compatible import to work with Django 1.4 timezone support
try:
    from django.utils.timezone import now
except ImportError:
    now = datetime.datetime.now

# Forward compatible import to work with old and new routing
try:
    from rapidsms.router import send
except ImportError:
    from rapidsms.contrib.messaging.utils import send_message
else:
    def send_message(connection, text):
        "Replicate old method signature."
        return send(text, connection=connection)
