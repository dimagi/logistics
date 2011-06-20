from django.conf import settings
from django.db.models import Q, Sum
from django.utils.importlib import import_module
from logistics.apps.logistics.const import Reports

if hasattr(settings,'LOGISTICS_CONFIG'):
    config = import_module(settings.LOGISTICS_CONFIG)
else:
    import config

def get_reporting_and_nonreporting_facilities(deadline, location):
    """
    Get all HSAs who haven't reported since a passed in date
    """
    if location is None:
        return None, None
    facilities = location.all_facilities()
    on_time_facilities = facilities.filter(Q(last_reported=None)|Q(last_reported__lt=deadline))
    late_facilities = facilities.filter(last_reported__gte=deadline)
    return on_time_facilities, late_facilities
