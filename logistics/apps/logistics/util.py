from django.conf import settings
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
    late_facilities = []
    on_time_facilities = []
    if location is None:
        return None, None
    facilities = location.all_facilities()
    for facility in facilities:
        if facility.last_reported is None or facility.last_reported <= deadline:
            late_facilities.append(facility)
        else:
            on_time_facilities.append(facility)
    return on_time_facilities, late_facilities
