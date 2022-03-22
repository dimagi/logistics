#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
To use the http backend, one needs to append 'http' to the list of 
available backends, like so:

    "my_http_backend" : {"ENGINE":  "rapidsms.backends.http", 
                "port": 8888,
                "gateway_url": "http://www.smsgateway.com",
                "params_outgoing": "user=my_username&password=my_password&id=%(phone_number)s&text=%(message)s",
                "params_incoming": "id=%(phone_number)s&text=%(message)s"
        }

"""

from future import standard_library
standard_library.install_aliases()
from builtins import str
import urllib.request, urllib.error, urllib.parse
import select
from datetime import datetime
from http.client import responses

from django import http
from django.http import HttpResponse, HttpResponseBadRequest
from django.core.handlers.wsgi import WSGIHandler
from django.core.servers.basehttp import WSGIServer, WSGIRequestHandler

from rapidsms.log.mixin import LoggerMixin
from rapidsms.backends.base import BackendBase


class RapidWSGIHandler(WSGIHandler, LoggerMixin):
    """ WSGIHandler without Django middleware and signal calls """

    def _logger_name(self):
        return "%s/%s" % (self.backend._logger_name(), 'handler')

    def __call__(self, environ, start_response):
        request = self.request_class(environ)
        self.debug('Request from %s' % request.get_host())
        try:
            response = self.backend.handle_request(request)
        except Exception as e:
            self.exception(e)
            response = http.HttpResponseServerError()
        status_text = responses.get(response.status_code, 'UNKNOWN STATUS CODE')
        status = '%s %s' % (response.status_code, status_text)
        response_headers = [(str(k), str(v)) for k, v in list(response.items())]
        start_response(str(status), response_headers)
        return response


class RapidHttpServer(WSGIServer):
    """ WSGIServer that doesn't block on handle_request """

    def handle_request(self, timeout=1.0):
        reads, writes, errors = (self, ), (), ()
        reads, writes, errors = select.select(reads, writes, errors, timeout)
        if reads:
            WSGIServer.handle_request(self)


class RapidHttpBackend(BackendBase):
    """ RapidSMS backend that creates and handles an HTTP server """

    _title = "HTTP"

    def configure(self, host="localhost", port=8080, 
                  gateway_url="http://smsgateway.com", 
                  params_outgoing="user=my_username&password=my_password&id=%(phone_number)s&text=%(message)s", 
                  params_incoming="id=%(phone_number)s&text=%(message)s"):
        self.host = host
        self.port = port
        self.handler = RapidWSGIHandler()
        self.handler.backend = self
        self.gateway_url = gateway_url
        self.http_params_outgoing = params_outgoing
        
        self.incoming_phone_number_param = None
        self.incoming_message_param = None
        key_value = params_incoming.split('&')
        for kv in key_value:
            key,val = kv.split('=')
            if val == "%(phone_number)s": 
                self.incoming_phone_number_param = key
            elif val == "%(message)s":
                self.incoming_message_param = key

    def run(self):
        server_address = (self.host, int(self.port))
        self.info('Starting HTTP server on {0}:{1}'.format(*server_address))
        self.server = RapidHttpServer(server_address, WSGIRequestHandler)
        self.server.set_app(self.handler)
        while self.running:
            self.server.handle_request()

    def handle_request(self, request):
        self.debug('Received request: %s' % request.GET)
        sms = request.GET.get(self.incoming_message_param, '')
        sender = request.GET.get(self.incoming_phone_number_param, '')
        if not sms or not sender:
            error_msg = 'ERROR: Missing %(msg)s or %(phone_number)s. parameters received are: %(params)s' % \
                         { 'msg' : self.incoming_message_param, 
                           'phone_number': self.incoming_phone_number_param,
                           'params': str(request.GET)
                         }
            self.warning(error_msg)
            return HttpResponseBadRequest(error_msg)
        now = datetime.utcnow()
        try:
            msg = super(RapidHttpBackend, self).message(sender, sms, now)
        except Exception as e:
            self.exception(e)
            raise        
        self.route(msg)
        return HttpResponse('OK') 
    
    def send(self, message):
        self.info('Sending message: %s' % message)
        text = message.text
        if isinstance(text, str):
            text = text.encode('utf-8')
        # we do this since http_params_outgoing is a user-defined settings
        # and we don't want things like "%(doesn'texist)s" to throw an error
        http_params_outgoing = self.http_params_outgoing.replace('%(message)s',
                                                                      urllib.parse.quote(text))
        http_params_outgoing = http_params_outgoing.replace('%(phone_number)s',
                                                                      urllib.parse.quote(message.connection.identity))
        url = "%s?%s" % (self.gateway_url, http_params_outgoing)
        try:
            self.debug('Sending: %s' % url)
            response = urllib.request.urlopen(url)
        except Exception as e:
            self.exception(e)
            return False
        self.info('SENT')
        info = 'RESPONSE %s' % response.info()
        info = info.replace('\n',' ').replace('\r',',')
        
        self.debug(info)
        return True
