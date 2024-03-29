#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from __future__ import unicode_literals
from ..utils.modules import try_import, get_class
from ..log.mixin import LoggerMixin


class AppBase(LoggerMixin):
    """
    """

    @classmethod
    def find(cls, app_name):
        """
        Return the RapidSMS app class from *app_name* (a standard Django
        app name), or None if it does not exist. Import errors raised
        *within* the module are allowed to propagate.
        """

        module_name = "%s.app" % app_name
        module = try_import(module_name)
        if module is None: return None
        return get_class(module, cls)


    def __init__(self, router):
        self.router = router

    def _logger_name(self): # pragma: no cover
        return "app/%s" % self.name

    @property
    def name(self):
        """
        Return the name of the module which this app was defined within.
        This can be considered a unique identifier with the project.
        """

        return self.__module__.split(".")[-2]

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<app: %s>" %\
            self.name

    # router events
    def start (self): pass
    def stop  (self): pass

    # incoming phases
    def filter   (self, msg): pass
    def parse    (self, msg): pass
    def handle   (self, msg): pass
    def default  (self, msg): pass
    def catch    (self, msg): pass
    def cleanup  (self, msg): pass

    # outgoing phases:
    def outgoing (self, msg): pass
