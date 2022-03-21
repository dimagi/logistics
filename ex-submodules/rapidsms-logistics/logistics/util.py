from __future__ import unicode_literals
from builtins import str
from importlib import import_module
from rapidsms.conf import settings
from re import findall
from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.models import Connection, Backend

config = import_module(settings.LOGISTICS_CONFIG)

if hasattr(settings, "CODE_CHARS_RANGE"):
    CODE_CHARS_RANGE = settings.CODE_CHARS_RANGE
else:
    CODE_CHARS_RANGE = (2,4) # from 2 to 4 characters per product code

NUMERIC_LETTERS = ("lLO", "110")


def ussd_push_backend():
    if not hasattr(ussd_push_backend, '_backend'):
        backend_name = getattr(settings, 'USSD_PUSH_BACKEND', None)
        if backend_name:
            ussd_push_backend._backend = Backend.objects.get(name=backend_name)
        else:
            ussd_push_backend._backend = None

    return ussd_push_backend._backend


def get_ussd_connection(fallback_connection):
    backend = ussd_push_backend()
    if not backend:
        return fallback_connection

    return Connection(
        backend=backend,
        identity=fallback_connection.identity,
        contact=fallback_connection.contact
    )


def ussd_msg_response(msg, template, **kwargs):
    response = OutgoingMessage(
        get_ussd_connection(msg.connection),
        template,
        **kwargs
    )
    msg.responses.append(response)
    return msg


def parse_report(val):
    """
    Takes a product report string, such as "zi 10 co 20 la 30", and parses it into a list of tuples
    of (code, quantity).

    See test_report_parse.py for usages.
    """

    def _cleanup(s):
        return str(s)

    numeric_trans = str('').maketrans(NUMERIC_LETTERS[0], NUMERIC_LETTERS[1])

    return [(x[0], int(x[1].translate(numeric_trans))) \
            for x in findall("\s*(?P<code>[A-Za-z]{%(minchars)d,%(maxchars)d})\s*(?P<quantity>[\-?0-9%(numeric_letters)s]+)\s*" % \
                                    {"minchars": CODE_CHARS_RANGE[0],
                                     "maxchars": CODE_CHARS_RANGE[1],
                                     "numeric_letters": NUMERIC_LETTERS[0]}, _cleanup(val))]
