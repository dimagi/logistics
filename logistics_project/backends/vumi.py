import copy
import json
import logging
import urllib2

from rapidsms.backends.base import BackendBase


logger = logging.getLogger(__name__)


class VumiBackend(BackendBase):
    """
    A RapidSMS backend for Vumi.

    http://vumi-go.readthedocs.org/en/latest/http_api.html
    """
    def configure(self, url, account_key, access_token, **kwargs):
        self.sendsms_url = url
        self.sendsms_user = account_key
        self.sendsms_pass = access_token
        self.url_opener = self.prepare_url_opener()

    def prepare_url_opener(self):
        """Construct URL opener with auth."""
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self.sendsms_url, self.sendsms_user, self.sendsms_pass)
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        return urllib2.build_opener(handler)

    def prepare_request(self, text, identity):
        """Construct outbound data for requests.post."""
        kwargs = {'url': self.sendsms_url,
                  'headers': {'content-type': 'application/json'}}
        payload = {
            'content': text,
            'to_addr': identity
        }
        if self.sendsms_user and self.sendsms_pass:
            kwargs['auth'] = (self.sendsms_user, self.sendsms_pass)
        kwargs['data'] = json.dumps(payload)
        return urllib2.Request(**kwargs)

    def send(self, message):
        identity = message.connection.identity
        text = message.text

        logger.debug('Sending message: %s' % text)
        req = self.prepare_request(text, identity)
        handle = self.url_opener.open(req)
        resp = handle.read()
        self.debug("vumi response: %s" % resp)
        return True
