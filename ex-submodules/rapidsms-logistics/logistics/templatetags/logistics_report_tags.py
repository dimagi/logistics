from __future__ import unicode_literals
from django import template
from django.template.loader import render_to_string
from rapidsms.conf import settings
from datetime import datetime, timedelta
from django.db.models.query_utils import Q
from logistics.models import SupplyPoint, StockRequest,\
    StockRequestStatus, Product, ProductStock, StockTransaction
from logistics.const import Reports
from django.db.models.aggregates import Count
from collections import defaultdict
from django.db.models.expressions import F
from logistics.context_processors import custom_settings
from logistics.tables import ShortMessageTable
from logistics.reports import ProductAvailabilitySummary, ProductAvailabilitySummaryByFacility, ProductAvailabilitySummaryByFacilitySP
from logistics_project.utils.dates import DateSpan, get_day_of_month
import rapidsms.contrib.messagelog as messagelog
import logging
from rapidsms.models import Contact
from logistics.models import transactions_before_or_during
from django.core.cache import cache

Message = messagelog.models.Message
register = template.Library()

def context_helper(context):
    extras = {
        "STATIC_URL": settings.STATIC_URL,
    }
    context.update(extras)
    context.update(custom_settings(None))
    return context
    
def r_2_s_helper(template, dict):
    return render_to_string(template, context_helper(dict))


@register.simple_tag
def order_fill_stats(locations, type=None, datespan=None):
    """
    With a list of locations - display reporting
    rates associated with those locations.
    This method only looks at closed orders
    """
    if locations:
        if datespan == None:
            # default to last 30 days
            datespan = DateSpan.since(30)
        base_points = SupplyPoint.objects.filter(location__in=locations, active=True)
        if type is not None:
            base_points = base_points.filter(type__code=type)
        if base_points.count() > 0:
            base_reqs = StockRequest.objects.filter(supply_point__in=base_points,
                                                    requested_on__gte=datespan.startdate, 
                                                    requested_on__lte=datespan.enddate)
            rec_reqs = base_reqs.filter(status=StockRequestStatus.RECEIVED)
            totals = base_reqs.values('product').annotate(total=Count('pk'))
            rec_totals = rec_reqs.values('product').annotate(total=Count('pk'))
            eo_totals = base_reqs.filter(is_emergency=True).values('product').annotate(total=Count('pk'))
            stocked_out = rec_reqs.filter(amount_received=0).values('product').annotate(total=Count('pk'))
            not_stocked_out = rec_reqs.filter(amount_received__gt=0).exclude(response_status=StockRequestStatus.STOCKED_OUT)
            under_supplied = not_stocked_out.filter(amount_requested__gt=F('amount_received')).values('product').annotate(total=Count('pk'))
            well_supplied = not_stocked_out.filter(amount_requested=F('amount_received')).values('product').annotate(total=Count('pk'))
            over_supplied = not_stocked_out.filter(amount_requested__lt=F('amount_received')).values('product').annotate(total=Count('pk'))
            main_data = {}
            for row in totals:
                main_data[row["product"]]=defaultdict(lambda x: 0)
                main_data[row["product"]]["product"] = Product.objects.get(pk=row["product"])
                main_data[row["product"]]["total"] = row["total"]
            
            def _update_main_data(main, to_update, tag):
                for row in to_update:
                    main[row["product"]][tag] = row["total"]
            
            _update_main_data(main_data, rec_totals, "filled")
            _update_main_data(main_data, eo_totals, "emergency")
            _update_main_data(main_data, stocked_out, "stocked_out")
            _update_main_data(main_data, under_supplied, "under_supplied")
            _update_main_data(main_data, well_supplied, "well_supplied")
            _update_main_data(main_data, over_supplied, "over_supplied")
            return r_2_s_helper("logistics/partials/order_fill_stats.html", 
                                    {"data": main_data,
                                     "datespan": datespan})
                                     
    return "" # no data, no report

@register.simple_tag
def stockonhand_table(supply_point, datespan=None):
    if datespan is None:
        datespan = DateSpan.since(settings.LOGISTICS_REPORTING_CYCLE_IN_DAYS)
    sohs = supply_point.stocked_productstocks().order_by('product__name')
    # update the stock quantities to match whatever reporting period has been specified
    for soh in sohs: 
        soh.quantity = supply_point.historical_stock_by_date(soh.product, datespan.end_of_end_day)
    return r_2_s_helper("logistics/partials/stockonhand_table_full.html", 
                         {"stockonhands": sohs, 
                          "datespan": datespan})
    
@register.simple_tag
def recent_messages(contact, limit=5):
    mdates = Message.objects.filter(contact=contact).order_by("-date").distinct().values_list("date", flat=True)
    if limit:
        mdates = list(mdates)[:limit]
    messages = Message.objects.filter(contact=contact, date__in=mdates).order_by("-date")
    return ShortMessageTable(messages).as_html()


@register.simple_tag
def product_availability_summary(location, width=900, height=300):
    if not location:
        # TODO: probably want to disable this if things get slow
        contacts = Contact.objects
    else:
        contacts = Contact.objects.filter(supply_point__location=location)
    
    summary = ProductAvailabilitySummary(contacts, width, height)
    return r_2_s_helper("logistics/partials/product_availability_summary.html", 
                         {"summary": summary})


@register.simple_tag
def commodity_code_to_name(code):
    try:
        return Product.objects.get(sms_code=code).name
    except Product.DoesNotExist:
        return "Unknown Commodity"


@register.simple_tag
def stock(supply_point, product, default_value=0):
    return supply_point.stock(product, default_value)


@register.simple_tag
def historical_stock(supply_point, product, year, month, default_value=0):
    return supply_point.historical_stock(product, year, month, default_value)


def _months_or_default(val, default_value):
    try:
        return "%0.2f" % val 
    except TypeError:
        return default_value

@register.simple_tag
def months_of_stock(supply_point, product, default_value=None):
    val = supply_point.months_of_stock(product, default_value)
    return _months_or_default(val, default_value)
