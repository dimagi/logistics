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
from logistics.views import get_location_children
from logistics.tables import ShortMessageTable
from logistics.reports import ReportingBreakdown,\
    ProductAvailabilitySummary, ProductAvailabilitySummaryByFacility, ProductAvailabilitySummaryByFacilitySP,\
    HSASupplyPointRow, FacilitySupplyPointRow, DynamicProductAvailabilitySummaryByFacilitySP
from dimagi.utils.dates import DateSpan, get_day_of_month
from logistics.config import messagelog
import logging
from rapidsms.models import Contact
from logistics.models import transactions_before_or_during
from django.core.cache import cache

Message = messagelog.models.Message
register = template.Library()

def context_helper(context):
    extras = {"MEDIA_URL": settings.MEDIA_URL}
    context.update(extras)
    context.update(custom_settings(None))
    return context
    
def r_2_s_helper(template, dict):
    return render_to_string(template, context_helper(dict))
    
@register.simple_tag
def aggregate_table(location, commodity_filter=None, commoditytype_filter=None, datespan=None):
    context = { "location": location, 
                "commodity_filter": commodity_filter,
                "commoditytype_filter": commoditytype_filter }
    context["rows"] = get_location_children(location, commodity_filter, commoditytype_filter, datespan)
    return r_2_s_helper("logistics/partials/aggregate_table.html", context)

@register.simple_tag
def hsa_aggregate_table(location, commodity_filter=None, commoditytype_filter=None):
    rows = [HSASupplyPointRow(SupplyPoint.objects.get(location=child), commodity_filter, commoditytype_filter)\
            for child in location.get_children().filter(supplypoint__contact__is_active=True)]
    return r_2_s_helper("logistics/partials/aggregate_table.html", {"rows": rows})

@register.simple_tag
def facility_aggregate_table(location, commodity_filter=None, commoditytype_filter=None):
    
    rows = [FacilitySupplyPointRow(SupplyPoint.objects.get(location=child), commodity_filter, commoditytype_filter)\
            for child in location.get_children()]
    return r_2_s_helper("logistics/partials/aggregate_table.html", {"rows": rows})


@register.simple_tag
def reporting_rates(locations, type=None, days=30):
    # with a list of locations - display reporting
    # rates associated with those locations
    if locations:
        since = datetime.utcnow() - timedelta(days=days)
        base_points = SupplyPoint.objects.filter(location__in=locations, active=True)
        if type is not None:
            base_points = base_points.filter(type__code=type)
        if base_points.count() > 0:
            late_facilities = base_points.filter(Q(last_reported__lt=since) | Q(last_reported=None)).order_by('-last_reported','name')
            on_time_facilities = base_points.filter(last_reported__gte=since).order_by('-last_reported','name')
            return r_2_s_helper("logistics/partials/reporting_rates.html", 
                                    {"late_facilities": late_facilities,
                                     "on_time_facilities": on_time_facilities,
                                     "graph_width": 200,
                                     "graph_height": 200,
                                     "days": days,
                                     "table_class": "minor_table" })
                                     
    return "" # no data, no report


@register.inclusion_tag("logistics/partials/reporting_breakdown.html", takes_context=True)
def reporting_breakdown(context, locations, type=None, datespan=None, include_late=False):
    # with a list of locations - display reporting
    # rates associated with those locations
    request = context['request']
    if locations:
        base_points = SupplyPoint.objects.filter(location__in=locations, active=True)
        if type is not None and type:
            base_points = base_points.filter(type__code=type)
        if base_points.count() > 0:
            report = ReportingBreakdown(base_points, datespan, request=request, include_late=include_late,
                                        days_for_late = settings.LOGISTICS_DAYS_UNTIL_LATE_PRODUCT_REPORT)
            context = {"report": report,
                       "graph_width": 200,
                       "graph_height": 200,
                       "datespan": datespan,
                       "table_class": "minor_table" }
            return context_helper(context)
                                     
    return "" # no data, no report



@register.simple_tag
def order_response_stats(locations, type=None, days=30):
    """
    With a list of locations - display reporting
    rates associated with those locations.
    This method only looks at closed orders
    """
    if locations:
        since = datetime.utcnow() - timedelta(days=days)
        base_points = SupplyPoint.objects.filter(location__in=locations, active=True)
        if type is not None:
            base_points = base_points.filter(type__code=type)
        if base_points.count() > 0:
            data = []
            for sp in base_points:
                this_sp_data = defaultdict(lambda x: 0)
                this_sp_data["supply_point"] = sp
                base_reqs = StockRequest.objects.filter(supply_point=sp, 
                                                        requested_on__gte=since)
                this_sp_data["total"] = base_reqs.aggregate(Count("pk"))["pk__count"]
                # by status
                by_status = base_reqs.values('response_status').annotate(total=Count('pk'))
                for row in by_status:
                    this_sp_data[row["response_status"] if row["response_status"] else "requested"] = row["total"]
                data.append(this_sp_data)
            return r_2_s_helper("logistics/partials/order_response_stats.html", 
                                    {"data": data })
                                     
            
    return "" # no data, no report
            
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
                                                    requested_on__lte=datespan.enddate, 
                                                    status=StockRequestStatus.RECEIVED)
            totals = base_reqs.values('product').annotate(total=Count('pk'))
            stocked_out = base_reqs.filter(amount_received=0).values('product').annotate(total=Count('pk'))
            not_stocked_out = base_reqs.filter(amount_received__gt=0).exclude(response_status=StockRequestStatus.STOCKED_OUT)
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
                         {"stockonhands": sohs})
    
@register.simple_tag
def recent_messages(contact, limit=5):
    mdates = Message.objects.filter(contact=contact).order_by("-date").distinct().values_list("date", flat=True)
    if limit:
        mdates = list(mdates)[:limit]
    messages = Message.objects.filter(contact=contact, date__in=mdates).order_by("-date")
    return ShortMessageTable(messages).as_html()

@register.simple_tag
def recent_messages_sp(sp, limit=5):
    mdates = Message.objects.filter(contact__in=sp.contact_set.all).order_by("-date").distinct().values_list("date", flat=True)
    if limit:
        mdates = list(mdates)[:limit]
    messages = Message.objects.filter(contact__in=sp.contact_set.all, date__in=mdates).order_by("-date")
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
def product_availability_summary_by_facility(location, width=900, height=300):
    if not location:
        pass
    summary = ProductAvailabilitySummaryByFacility(location.all_child_facilities(),
                                                   width, height)
    c =  r_2_s_helper("logistics/partials/product_availability_summary.html",
                         {"summary": summary})
    return c

@register.simple_tag
def product_availability_summary_by_facility_sp(location, year, month):
    if not location:
        pass
    summary = ProductAvailabilitySummaryByFacilitySP(location.all_child_facilities(), year=year, month=month)
    c =  r_2_s_helper("logistics/partials/product_availability_summary.html",
                         {"summary": summary})
    return c


def commodity_filter(commodities, can_select_all=True):
    return render_to_string("logistics/partials/commodity_filter.html", {"commodities": commodities, 
                                                                         "can_select_all": can_select_all})

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

@register.simple_tag
def historical_months_of_stock(supply_point, product, year, month, default_value=None):
    def _cache_key():
            return ("log-historical_months_of_stock-%(supply_point)s-%(product)s-%(year)s-%(month)s-%(default)s" % \
                    {"supply_point": supply_point.code, "product": product.sms_code, 
                     "year": year, "month": month, "default": default_value}).replace(" ", "-")
    key = _cache_key()
    if settings.LOGISTICS_USE_SPOT_CACHING: 
        from_cache = cache.get(key)
        if from_cache:
            return from_cache
            
        
    srs = transactions_before_or_during(year, month).\
                filter(supply_point=supply_point, product=product).order_by("-date")
    if srs.exists():
        val = ProductStock.objects.get(supply_point=supply_point, product=product)\
                    .calculate_months_remaining(srs[0].ending_balance)
        ret = _months_or_default(val, default_value)
    else: 
        ret = default_value
    if settings.LOGISTICS_USE_SPOT_CACHING: 
            cache.set(key, ret, settings.LOGISTICS_SPOT_CACHE_TIMEOUT)
    return ret
