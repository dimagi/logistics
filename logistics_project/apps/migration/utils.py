#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from __future__ import unicode_literals
from django.utils.functional import curry
from rapidsms.contrib.ajax.utils import call_router

# these helper methods are just proxies to app.py
send_test_message = curry(call_router, "migration", "send")
check_status = curry(call_router, "migration", "status")
