"""
To use the Kannel backend, one needs to append 'kannel' to the list of 
available backends, like so:

INSTALLED_BACKENDS.update({
    "fake" : {
        "ENGINE":  "rapidsms.backends.kannel",
        "host": "127.0.0.1",
        "port": 8081,
        "sendsms_url": "http://127.0.0.1:13013/cgi-bin/sendsms",
        "sendsms_params": {"smsc": "FAKE",
                           "from": "88160", # not set automatically by SMSC
                           "username": "tester",
                           "password": "foobar"},
        "coding": 0,
        "charset": "ascii",
        "encode_errors": "ignore", # strip out unknown (unicode) characters
    }
})
    
The associated Kannel settings might look something like this:

# start the fake SMSC for testing on port 20000:
group = smsc
smsc = fake
smsc-id = FAKE
port = 20000
connect-allow-ip = 127.0.0.1

# listen for outgoing messages from RapidSMS:
group = smsbox
sendsms-port = 13013
# .... other smsbox options here

# add a user for RapidSMS to connect as:
group = sendsms-user
username = tester
password = foobar
user-deny-ip = "*.*.*.*"
user-allow-ip = "127.0.0.1"

# deliver inbound messages to RapidSMS:
group = sms-service
keyword = default
accepted-smsc = FAKE
# don't send a reply here (it'll come through sendsms):
max-messages = 0
get-url = http://127.0.0.1:8081/?id=%p&text=%a&charset=%C&coding=%c
"""
from __future__ import unicode_literals

from django.db import close_old_connections
from future import standard_library
standard_library.install_aliases()
from builtins import str
import copy
import urllib.request, urllib.parse, urllib.error
from urllib.request import urlopen

from datetime import datetime

from django.http import HttpResponse, HttpResponseBadRequest
from rapidsms.backends.http import RapidHttpBackend

class KannelBackend(RapidHttpBackend):
    """
    Backend for use with the Kannel SMS Gateway.
    """

    def configure(self, sendsms_url='http://127.0.0.1:13013/cgi-bin/sendsms',
                  sendsms_params=None, charset=None, coding=None,
                  encode_errors=None, **kwargs):
        self.sendsms_url = sendsms_url
        self.sendsms_params = sendsms_params or {}
        self.charset = charset or 'ascii'
        self.coding = coding or 0
        self.encode_errors = encode_errors or 'ignore'
        super(KannelBackend, self).configure(**kwargs)

    def handle_request(self, request):
        self.debug('Received request: %s' % request.GET)
        close_old_connections()
        sms = request.GET.get('text', None)
        sender = request.GET.get('id', None)
        coding = request.GET.get('coding', None)
        charset = request.GET.get('charset', None)
        if sms is None or sender is None:
            error_msg = 'ERROR: Missing "text" or "id" params. '\
                        'parameters received are: %(params)s' % \
                         {'params': str(request.GET)}
            self.error(error_msg)
            return HttpResponseBadRequest(error_msg)
        now = datetime.utcnow()
        # UTF-8 (and possible other charsets) will already be decoded, while
        # UTF-16BE will not, so decode them manually here if we don't already
        # have a unicode string
        if charset and not isinstance(sms, str):
            sms = sms.decode(charset)
        try:
            msg = super(RapidHttpBackend, self).message(sender, sms, now)
        except:
            self.exception('failed to create message in RapidSMS')
            raise
        self.route(msg)
        return HttpResponse('') # any response would get sent to the user

    def send(self, message):
        self.info('Sending message: %s' % message)
        url_args = copy.copy(self.sendsms_params)
        url_args['to'] = message.connection.identity
        url_args['text'] = message.text.encode(self.charset,
                                               self.encode_errors)
        url_args['coding'] = self.coding
        url_args['charset'] = self.charset
        url = '?'.join([self.sendsms_url, urllib.parse.urlencode(url_args)])
        try:
            self.debug('Opening URL: %s' % url)
            with urlopen(url) as response:
                self.info('SENT')
                self.debug('response body: %s' % response.read())
                return True
        except Exception:
            self.exception('Failed to send message')
            return
