#!/usr/bin/env python
# vim: et ts=4 sw=4


# hackery: since this column uses a django template filter, we must
# configure the django settings explicitly before testing it.
from __future__ import unicode_literals
def setup():
    from django.conf import settings
    settings.configure()
