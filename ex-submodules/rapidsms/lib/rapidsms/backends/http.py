#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
To use the http backend, one needs to append 'http' to the list of 
available backends, like so:

    "txtnation" : {"ENGINE":  "rapidsms.backends.http",
            "port": 8888,
            "gateway_url": "http://client.txtnation.com/mbill.php",
            "params_outgoing": "reply=%(reply)s&id=%(id)s&network=%(network)s&number=%(phone_number)s&message=%(message)s&ekey=<SEKRIT_KEY>&cc=dimagi&currency=THB&value=0&title=trialcnct",
            "params_incoming": "action=action&id=%(id)s&number=%(phone_number)s&network=%(network)s&message=%(message)s&shortcode=%(sc)s&country=%(country_code)&billing=%(bill_code)s"
    },
"""

import urllib2
import urllib
import select
from datetime import datetime

from django import http
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.core.handlers.wsgi import WSGIHandler, STATUS_CODE_TEXT
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
        except Exception, e:
            self.exception(e)
            response = http.HttpResponseServerError()
        try:
            status_text = STATUS_CODE_TEXT[response.status_code]
        except KeyError:
            status_text = 'UNKNOWN STATUS CODE: %s' % str(response.status_code)
        status = '%s %s' % (response.status_code, status_text)
        response_headers = [(str(k), str(v)) for k, v in response.items()]
        start_response(status, response_headers)
        return response


class RapidHttpServer(WSGIServer):
    """ WSGIServer that doesn't block on handle_request """

    def handle_request(self, timeout=1.0):
        reads, writes, errors = (self, ), (), ()
        reads, writes, errors = select.select(reads, writes, errors, timeout)
        if reads:
            WSGIServer.handle_request(self)


class RapidHttpBacked(BackendBase):
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
        self.outgoing_network_param = None
        self.outgoing_ekey_param = None
        self.outgoing_cc_param = None
        self.outgoing_currency_param = None
        self.outgoing_value_param = None
        self.outgoing_title_param = None
        key_value = params_incoming.split('&')
        for kv in key_value:
            key,val = kv.split('=')
            if key == 'network':
                self.outgoing_network_param = val
            if key == 'ekey':
                self.outgoing_ekey_param = val
            if key == 'cc':
                self.outgoing_cc_param = val
            if key == 'value':
                self.outgoing_value_param = val
            if key == 'title':
                self.outgoing_title_param = val

        self.incoming_action_param = None
        self.incoming_network_param = None
        self.incoming_id_param = None
        self.incoming_phone_number_param = None
        self.incoming_message_param = None
        self.incoming_shortcode_param = None
        self.incoming_country_param = None
        self.incoming_billing_param = None
        key_value = params_incoming.split('&')
        for kv in key_value:
            key,val = kv.split('=')
            if val == "%(phone_number)s": 
                self.incoming_phone_number_param = key
            elif val == "%(message)s":
                self.incoming_message_param = key
            elif val == "%(action)s":
                self.incoming_action_param = key
            elif val == "%(network)s":
                self.incoming_network_param = key
            elif val == "%(id)s":
                self.incoming_id_param = key
            elif val == "%(sc)s":
                self.incoming_shortcode_param = key
            elif val == "%(country_code)s":
                self.incoming_country_param = key
            elif val == "%(bill_code)s":
                self.incoming_billing_param = key

    def run(self):
        server_address = (self.host, int(self.port))
        self.info('Starting HTTP server on {0}:{1}'.format(*server_address))
        self.server = RapidHttpServer(server_address, WSGIRequestHandler)
        self.server.set_app(self.handler)
        while self.running:
            self.server.handle_request()

    def handle_request(self, request):
        if request.method != 'POST':
            self.info('Received request but wasn\'t POST. Doing nothing: %s' % request.GET)
            return HttpResponseNotAllowed()

        if 'report' in request.POST:
            self.delivery_report(request)
        self.info('Received request: %s' % request.POST)
        sms = request.POST.get(self.incoming_message_param, '')
        sender = request.POST.get(self.incoming_phone_number_param, '')
        if not sms or not sender:
            error_msg = 'ERROR: Missing %(msg)s or %(phone_number)s. parameters received are: %(params)s' % \
                         { 'msg' : self.incoming_message_param, 
                           'phone_number': self.incoming_phone_number_param,
                           'params': unicode(request.POST)
                         }
            self.error(error_msg)
            return HttpResponseBadRequest(error_msg)
        now = datetime.utcnow()
        try:
            msg = super(RapidHttpBacked, self).message(sender, sms, now)
        except Exception, e:
            self.exception(e)
            raise        
        self.route(msg)
        return HttpResponse('OK') 
    
    def send(self, message):
        self.info('Sending message: %s' % message)
        # if you wanted to add timestamp or any other outbound variable, 
        # you could add it to this context dictionary
        context = {'message':message.text,
                   'phone_number':message.connection.identity,
                   'id': message.id,
                    'reply':str(0), #rapidsms makes no attempt to track if a message is a reply or not so we don't either
                    'network':self.outgoing_network_param,
                    'ekey':self.outgoing_ekey_param,
                    'cc':self.outgoing_cc_param,
                    'cuurency':self.outgoing_currency_param,
                    'value':self.outgoing_value_param,
                    'title':self.outgoing_title_param,
                    }
        url = self.gateway_url
        data = urllib.urlencode(data)
        try:
            req = urllib2.Request(url, data)
            self.debug('Sending:: URL: %s, %s' % (url, str(context)))
            response = urllib2.urlopen(req)
        except Exception, e:
            self.exception(e)
            return
        self.info('SENT')
        self.debug(response)

    def delivery_report(self, request):
        '''
        Deals with delivery reports from TxTNation
        '''
        self.info("Delivery Report recieved.  Saving: %s" % str(request.POST))
        from rapidsms.models import DeliveryReport
        d = DeliveryReport(action=request.POST('action'),report_id=request.POST('id'),number=request.POST('number'),report=request.POST('report'))
        d.save()

#"params_outgoing": "reply=%(reply)s&id=%(id)s&network=%(network)s&number=%(phone_number)s&message=%(message)s&ekey=<SEKRIT_KEY>&cc=dimagi&currency=THB&value=0&title=trialcnct",
#"params_outgoing": "reply=%(reply)s&id=%(id)s&network=%(network)s&number=%(phone_number)s&message=%(message)s&ekey=<SEKRIT_KEY>&cc=dimagi&currency=THB&value=0&title=trialcnct",