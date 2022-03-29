#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from __future__ import unicode_literals
from rapidsms.backends.base import BackendBase


class MessageTestBackend(BackendBase):
    """
    Mock backend, for dispatching incoming messages from the WebUI.
    """

    pass
