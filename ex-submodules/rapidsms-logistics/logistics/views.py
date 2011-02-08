#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404s, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings
from django.utils.translation import ugettext as _

def dashboard(request, template):
    return HttpResponse("OK")
