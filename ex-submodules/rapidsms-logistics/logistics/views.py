#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from django.contrib.auth.models import User
from logistics.const import Reports

import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from logistics_project.apps.malawi.util import get_user_profile
from rapidsms.conf import settings
from rapidsms.contrib.locations.models import Location
from rapidsms.contrib.messagelog.views import message_log as rapidsms_messagelog
from logistics_project.utils.dates import DateSpan
from logistics_project.utils.decorators.datespan import datespan_in_request
from logistics.charts import stocklevel_plot
from logistics.decorators import place_in_request
from logistics.models import ProductStock, \
    ProductReportsHelper, ProductReport, LogisticsProfile,\
    SupplyPoint, StockTransaction
from logistics.util import config
from logistics.view_decorators import filter_context, geography_context
from logistics.reports import get_reporting_and_nonreporting_facilities
from .models import Product
from .forms import FacilityForm, CommodityForm
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Backend, Contact



def no_ie_allowed(request, template="logistics/no_ie_allowed.html"):
    return render_to_response(template, context_instance=RequestContext(request))

class JSONDateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return "Date(%d, %d, %d)" % (obj.year, obj.month, obj.day)
        else:
            return json.JSONEncoder.default(self, obj)

@csrf_exempt
@cache_page(60 * 15)
@require_POST
def navigate(request):
    location_code = settings.COUNTRY
    destination = "logistics_dashboard"
    querystring = ''
    if 'location' in request.REQUEST and request.REQUEST['location']: 
        location_code = request.REQUEST['location']
    if 'destination_url' in request.REQUEST and request.REQUEST['destination_url']: 
        destination = request.REQUEST['destination_url']
    if 'year' in request.REQUEST and request.REQUEST['year']: 
        querystring += '&year=' + request.REQUEST['year']
    if 'month' in request.REQUEST and request.REQUEST['month']: 
        querystring += '&month=' + request.REQUEST['month']
    if 'to' in request.REQUEST and request.REQUEST['to']: 
        querystring += '&to=' + request.REQUEST['to']
    if 'from' in request.REQUEST and request.REQUEST['from']: 
        querystring += '&from=' + request.REQUEST['from']
    mode = request.REQUEST.get("mode", "url")
    if mode == "url":
        return HttpResponseRedirect(
            reverse(destination, args=(location_code, )))
    elif mode == "param":
        return HttpResponseRedirect(
            "%s?place=%s%s" % (reverse(destination), location_code, querystring))
    elif mode == "direct-param":
        return HttpResponseRedirect(
            "%s?place=%s%s" % (destination, location_code, querystring))

@datespan_in_request()
def message_log(request, context={}, template="messagelog/index.html"):
    """
    NOTE: this truncates the messagelog by default to the last 30 days. 
    To get the complete message log, web users should export to excel 
    """
    messages = Message.objects.all()
    if 'messages_qs' in context:
        messages = context['messages_qs']
    if request.datespan is not None and request.datespan:
        messages = messages.filter(date__gte=request.datespan.startdate)\
          .filter(date__lte=request.datespan.end_of_end_day)
    context['messages_qs'] = messages
    return rapidsms_messagelog(request, context=context, 
                               template=template)

def messages_by_carrier(request, template="logistics/messages_by_carrier.html"):
    earliest_msg = Message.objects.all().order_by("date")[0].date
    month = earliest_msg.month
    year = earliest_msg.year
    backends = list(Backend.objects.all())
    counts = {}
    mdates = []
    d = datetime(year, month, 1) + relativedelta(months=1)-relativedelta(seconds=1)
    while d <= datetime.utcnow() + relativedelta(months=1):
        mdates += [d]
        counts[d] = {}
        for b in backends:
            counts[d][b.name] = {}
            counts[d][b.name]["in"] = Message.objects.filter(connection__backend=b, date__month=d.month, date__year=d.year, direction="I").count()
            counts[d][b.name]["out"] = Message.objects.filter(connection__backend=b, date__month=d.month, date__year=d.year, direction="O").count()
        d += relativedelta(months=1)
    mdates.reverse()
    return render_to_response(template,
                              {"backends": backends,
                               "counts": counts,
                               "mdates": mdates},
                              context_instance=RequestContext(request))

class MonthPager(object):
    """
    Utility class to show a month pager, e.g. << August 2011 >>
    """
    def __init__(self, request):
        self.month = int(request.GET.get('month', datetime.utcnow().month))
        self.year = int(request.GET.get('year', datetime.utcnow().year))
        self.begin_date = datetime(year=self.year, month=self.month, day=1)
        self.end_date = (self.begin_date + timedelta(days=32)).replace(day=1) - timedelta(seconds=1) # last second of previous month
        self.prev_month = self.begin_date - timedelta(days=1)
        self.next_month = self.end_date + timedelta(days=1)
        self.show_next = True if self.end_date < datetime.utcnow().replace(day=1) else False
        self.datespan = DateSpan(self.begin_date, self.end_date)


def global_stats(request):
    active_sps = SupplyPoint.objects.filter(active=True)
    hsa_type = getattr(config.SupplyPointCodes, 'HSA', 'nomatch')
    facility_type = getattr(config.SupplyPointCodes,'FACILITY', 'nomatch')
    context = {
        'supply_points': active_sps.count(),
        'facilities': active_sps.filter(type__code=facility_type).count(),
        'hsas': active_sps.filter(type__code=hsa_type).count(),
        'contacts': Contact.objects.filter(is_active=True).count(),
        'product_stocks': ProductStock.objects.filter(is_active=True).count(),
        'stock_transactions': StockTransaction.objects.count(),
        'inbound_messages': Message.objects.filter(direction='I').count(),
        'outbound_messages': Message.objects.filter(direction='O').count(),
        'products': Product.objects.count(),
        'web_users': User.objects.count()
    }
    return render_to_response('logistics/global_stats.html', context,
                              context_instance=RequestContext(request))
