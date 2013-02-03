""" This file defines functions used to generate message groups."""
try:
    # python 2.7 up
    from collections import OrderedDict
except ImportError:
    # below python 2.7, need to 'pip install ordereddict'
    from ordereddict import OrderedDict
from django.db.models.query_utils import Q
from rapidsms.contrib.locations.models import Location
from logistics.util import config

def below_location(location):
    return {location.name: 
            Q(supply_point__pk__in=[f.pk for f in location.all_facilities()])}

def by_district():
    """ return an ordered dictionary listing all districts """
    r = OrderedDict()
    locs = Location.objects.filter(type__slug=config.LocationCodes.DISTRICT)\
                           .order_by('code')
    for d in locs:
        r.update(below_location(d))
    return "Districts", r

def by_facility():
    """ return an ordered dictionary listing all facilities """
    r = OrderedDict()
    locs = Location.objects.filter(type__slug=config.LocationCodes.FACILITY)\
                           .order_by('name')
    for d in locs:
        r.update(below_location(d))
    return "Facilities", r
