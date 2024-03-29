#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from __future__ import unicode_literals
from builtins import str
from rapidsms.contrib.ajax.utils import call_router

def send_message(connection, text):
    """
    Send a message from the webui process to the router process,
    via the ajax app.
    """
    post = {"connection_id": str(connection.id), "text": text}
    return call_router("messaging", "send_message", **post)

