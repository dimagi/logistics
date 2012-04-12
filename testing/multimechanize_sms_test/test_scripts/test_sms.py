import httplib
import mechanize
from random import randint
import time
import urllib

class Transaction(object):

    def __init__(self):
        self.custom_timers = {}

    def run(self):
        mynumber = randint(1000000, 9999999)



        br = mechanize.Browser()
        br.set_handle_robots(False)
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        conn = httplib.HTTPConnection('localhost:8081')

        def _send(text):
            timer = text.split(" ")[0]
            post_body=urllib.urlencode({
                'MobileNumber': mynumber,
                'Text': text})
            start_timer = time.time()
            conn.request('POST', '/', post_body, headers)
            resp = conn.getresponse()
            latency = time.time() - start_timer
            self.custom_timers[timer] = latency
            assert (resp.status == 200), 'Bad Response: HTTP %s' % resp.status

        _send("register some test name D30702")
        _send("language en")
        _send("soh cond 100 dp 100 ip 100 cc 100 pp 11 ab 11 eo 23 al 23 ca 304 ZS 3923 qi 40")
        _send("supervision yes")
        _send("submitted")
        _send("help")
