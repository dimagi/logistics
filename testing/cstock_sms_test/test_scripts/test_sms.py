from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import object
import http.client
import mechanize
from random import randint
import time
import urllib.request, urllib.parse, urllib.error
import random

BACKEND_URL = 'localhost:9988'

class Transaction(object):

    def __init__(self):
        self.custom_timers = {}

    def run(self):
        mynumber = randint(1000000, 9999999)

        br = mechanize.Browser()
        br.set_handle_robots(False)
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        conn = http.client.HTTPConnection(BACKEND_URL)

        def _send(text):
            timer = text.split(" ")[0]
            params = urllib.parse.urlencode({
                'id': mynumber,
                'text': text,
            })
            start_timer = time.time()
            conn.request('GET', '/?%s' % params, None, headers)
            resp = conn.getresponse()
            latency = time.time() - start_timer
            self.custom_timers[timer] = latency
            assert (resp.status == 200), 'Bad Response: HTTP %s' % resp.status

        # representative message
        _r = lambda: random.randint(0, 99)
        msgs = [
            'register wendy {id} 2616'.format(id=_r()),
            'add LA LB CO PA OR ZI TE PB',
            'SOH LA 15 LB 60 CO 220 PA 270 OR 12 ZI 130 TE 7 PB 0',
            'REC LA 15 LB 60 CO 220 PA 270 OR 12 ZI 130 TE 7 PB 0',
            'quit',
        ]
        for msg in msgs:
            _send(msg)
            time.sleep(1)
