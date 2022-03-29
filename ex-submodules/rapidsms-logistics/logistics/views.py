from __future__ import unicode_literals
from django.contrib.auth.models import User

from django.shortcuts import render
from rapidsms.contrib.messagelog.views import message_log as rapidsms_messagelog
from logistics_project.utils.decorators.datespan import datespan_in_request
from logistics.models import ProductStock, \
    SupplyPoint, StockTransaction
from logistics.util import config
from .models import Product
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Contact


def no_ie_allowed(request, template="logistics/no_ie_allowed.html"):
    return render(request, template)


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
    return render(request, 'logistics/global_stats.html', context)
