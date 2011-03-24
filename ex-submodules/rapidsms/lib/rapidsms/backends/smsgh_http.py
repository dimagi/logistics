#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
A subclass of the http backend for SMSGH in Ghana
"""
from django.http import HttpResponse, HttpResponseBadRequest
from rapidsms.backends.http import RapidHttpBackend

class SmsghHttpBackend(RapidHttpBackend):
    """ RapidSMS backend that creates and handles an HTTP server """

    _title = "SMSGH_HTTP"

    def handle_request(self, request):
        """ The only difference is that we don't respond with 'OK' """
        response = super(SmsghHttpBackend, self).handle_request(request)
        if isinstance(response, HttpResponseBadRequest):
            return response
        return HttpResponse()
