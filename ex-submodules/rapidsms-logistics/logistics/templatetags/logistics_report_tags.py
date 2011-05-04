from django import template
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime, timedelta
from django.db.models.query_utils import Q
from logistics.apps.logistics.models import SupplyPoint, StockRequest,\
    StockRequestStatus, Product
from django.db.models.aggregates import Count
from collections import defaultdict
from django.db.models.expressions import F
register = template.Library()

@register.simple_tag
def reporting_rates(locations, type=None, days=30):
    # with a list of locations - display reporting
    # rates associated with those locations
    if locations:
        since = datetime.utcnow() - timedelta(days=days)
        base_points = SupplyPoint.objects.filter(location__in=locations)
        if type is not None:
            base_points = base_points.filter(type__code=type)
        if base_points.count() > 0:
            late_facilities = base_points.filter(Q(last_reported__lt=since) | Q(last_reported=None)).order_by('-last_reported','name')
            on_time_facilities = base_points.filter(last_reported__gte=since).order_by('-last_reported','name')
            return render_to_string("logistics/partials/reporting_rates.html", 
                                    {"late_facilities": late_facilities,
                                     "on_time_facilities": on_time_facilities,
                                     "graph_width": 200,
                                     "graph_height": 200,
                                     "days": days,
                                     "table_class": "minor_table",
                                     "MEDIA_URL": settings.MEDIA_URL})
    return "" # no data, no report

@register.simple_tag
def order_fill_stats(locations, type=None, days=30):
    # with a list of locations - display reporting
    # rates associated with those locations
    if locations:
        since = datetime.utcnow() - timedelta(days=days)
        base_points = SupplyPoint.objects.filter(location__in=locations)
        if type is not None:
            base_points = base_points.filter(type__code=type)
        if base_points.count() > 0:
            base_reqs = StockRequest.objects.filter(supply_point__in=base_points, 
                                                    requested_on__gte=since, 
                                                    status__in=StockRequestStatus.CHOICES_CLOSED)
            totals = base_reqs.values('product').annotate(total=Count('pk'))
            stocked_out = base_reqs.filter(amount_received=0).values('product').annotate(total=Count('pk'))
            under_supplied = base_reqs.filter(amount_received__gt=0,amount_requested__gt=F('amount_received')).values('product').annotate(total=Count('pk'))
            well_supplied = base_reqs.filter(amount_received__gt=0,amount_requested=F('amount_received')).values('product').annotate(total=Count('pk'))
            over_supplied = base_reqs.filter(amount_received__gt=0,amount_requested__lt=F('amount_received')).values('product').annotate(total=Count('pk'))
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
            return render_to_string("logistics/partials/order_fill_stats.html", 
                                    {"data": main_data,
                                     "MEDIA_URL": settings.MEDIA_URL})
    return "" # no data, no report