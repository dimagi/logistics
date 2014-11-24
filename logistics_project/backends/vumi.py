import copy
import json
import logging
import urllib2
import requests

from rapidsms.backends.base import BackendBase


logger = logging.getLogger(__name__)


class VumiBackend(BackendBase):
    """
    A RapidSMS backend for Vumi.

    http://vumi-go.readthedocs.org/en/latest/http_api.html
    Backport form: https://github.com/rapidsms/rapidsms/blob/develop/rapidsms/backends/vumi/outgoing.py
    """
    def configure(self, url, conversation_id, account_key, access_token, **kwargs):
        self.sendsms_url = url.format(conversation_id=conversation_id)
        self.sendsms_user = account_key
        self.sendsms_pass = access_token

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
        return kwargs

    def send(self, message):
        identity = message.connection.identity
        text = message.text

        logger.debug('Sending message: %s' % text)

        kwargs = self.prepare_request(text, identity)
        r = requests.put(**kwargs)
        logger.debug('Vumi response: %s', r.text)
        if r.status_code != requests.codes.ok:
            r.raise_for_status()
