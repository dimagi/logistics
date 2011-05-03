from django import template
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime, timedelta
from django.db.models.query_utils import Q
from logistics.apps.logistics.models import SupplyPoint
register = template.Library()

@register.simple_tag
def reporting_rates(locations, type=None):
    # with a list of locations - display reporting
    # rates associated with those locations
    if locations:
        since = datetime.utcnow() - timedelta(days=30)
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
                                     "table_class": "minor_table",
                                     "MEDIA_URL": settings.MEDIA_URL})
    return "" # no data, no report