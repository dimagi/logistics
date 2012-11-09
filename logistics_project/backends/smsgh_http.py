#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
A subclass of the http backend for SMSGH in Ghana
"""
import urllib2
from datetime import datetime
from django.http import HttpResponse, HttpResponseBadRequest
from rapidsms.backends.http import RapidHttpBackend
from rapidsms.messages.incoming import IncomingMessage

DEFAULT_SHORTCODE = '1902'
 
class SmsghHttpBackend(RapidHttpBackend):
    """ RapidSMS backend that creates and handles an HTTP server """

    _title = "SMSGH_HTTP"

    def _message(self, identity, text, received_at=None, to=None):
        from rapidsms.models import Connection
        conn, created = Connection.objects.get_or_create(
            backend=self.model,
            identity=identity)
        conn.to = to
        conn.save()
        return IncomingMessage(
            conn, text, received_at)

    def handle_request(self, request):
        self.error('Received request: %s' % request.GET)
        sms = request.GET.get(self.incoming_message_param, '')
        sender = request.GET.get(self.incoming_phone_number_param, '')
        to = request.GET.get('to', None)
        if not sms or not sender:
            error_msg = 'ERROR: Missing %(msg)s or %(phone_number)s. parameters received are: %(params)s' % \
                         { 'msg' : self.incoming_message_param, 
                           'phone_number': self.incoming_phone_number_param,
                           'params': unicode(request.GET)
                         }
            self.warning(error_msg)
            return HttpResponseBadRequest(error_msg)
        now = datetime.utcnow()
        try:
            msg = self._message(sender, sms, now, to)
        except Exception, e:
            self.exception(e)
            raise        
        self.route(msg)
        return HttpResponse()

    def send(self, message):
        self.info('Sending message: %s' % message)
        text = message.text
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        # we do this since http_params_outgoing is a user-defined settings
        # and we don't want things like "%(doesn'texist)s" to throw an error
        http_params_outgoing = self.http_params_outgoing.replace('%(message)s',
            urllib2.quote(text))
        http_params_outgoing = http_params_outgoing.replace('%(phone_number)s',
            urllib2.quote(message.connection.identity))
        from_number = message.connection.to if message.connection.to else DEFAULT_SHORTCODE
        http_params_outgoing = http_params_outgoing.replace('%(from)s',
            urllib2.quote(from_number))
        url = "%s?%s" % (self.gateway_url, http_params_outgoing)
        try:
            self.error('Sending: %s' % url)
            response = urllib2.urlopen(url)
        except Exception, e:
            self.exception(e)
            return False
        self.info('SENT')
        info = 'RESPONSE %s' % response.info()
        info = info.replace('\n',' ').replace('\r',',')
        
        self.debug(info)
        return True
