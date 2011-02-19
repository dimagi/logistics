#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from logistics.apps.logistics.models import Location, ProductStock

def input_stock(request, template="logistics/input_stock.html"):
    context = {}
    # TODO: replace this with something that depends on the current user
    rms = Location.objects.filter(type__slug='RMS')[0]
    context['commodities'] = [p.product for p in ProductStock.objects.filter(location=rms, is_active=True).order_by('product')]
    context['date'] = datetime.now()
    return render_to_response(
        template, context, context_instance=RequestContext(request)
    )

def stockonhand(request, facility_code, template="logistics/stockonhand.html"):
    """
     TODO: this view currently only shows the current stock on hand
     It would be great to show historical stock on hand
    """
    context = {}
    location = get_object_or_404(Location, code=facility_code)
    stockonhands = ProductStock.objects.filter(location=location, is_active=True).order_by('product')
    context['stockonhands'] = stockonhands
    return render_to_response(
        template, context, context_instance=RequestContext(request)
    )
