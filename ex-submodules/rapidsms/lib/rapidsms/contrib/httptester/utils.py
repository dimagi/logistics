from functools import partialmethod
from rapidsms.contrib.ajax.utils import call_router


# these helper methods are just proxies to app.py
send_test_message = partialmethod(call_router, "httptester", "send")
get_message_log = partialmethod(call_router, "httptester", "log")
