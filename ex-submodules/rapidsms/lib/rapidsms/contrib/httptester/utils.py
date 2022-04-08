from functools import partial
from rapidsms.contrib.ajax.utils import call_router


# these helper methods are just proxies to app.py
send_test_message = partial(call_router, "httptester", "send")
get_message_log = partial(call_router, "httptester", "log")
