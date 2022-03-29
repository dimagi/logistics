from __future__ import unicode_literals
# This file defines functions used to generate message groups.
from django.db.models.query_utils import Q
from logistics_project.apps.malawi.util import hsa_supply_points_below
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact


def below_location(location):
    return {location.name: Q(supply_point__location=location) |
                           Q(supply_point__supplied_by__location=location) | 
                           Q(supply_point__supplied_by__supplied_by__location=location)}


def by_district():
    r = {}
    for d in Location.objects.filter(type="district"):
        r.update(below_location(d))
    return "Districts", r

def by_facility():
    r = {}
    for d in Location.objects.filter(type="facility").order_by("parent_id"):
        r.update(below_location(d))
    return "Facilities", r
