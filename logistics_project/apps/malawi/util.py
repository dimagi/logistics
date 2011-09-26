from rapidsms.models import Contact
from logistics.models import SupplyPoint
from logistics.util import config
from logistics_project.apps.malawi.exceptions import MultipleHSAException
from rapidsms.contrib.locations.models import Location
from django.db.models.query_utils import Q


def get_hsa(hsa_id):
    """
    Attempt to get an HSA by code, return None if unable to find them.
    """
    # in the future we should do some massaging of this code as well
    # to catch things like o's -> 0's and such.
    try:
        sp = SupplyPoint.objects.get(active=True, code=hsa_id, type=config.hsa_supply_point_type())
        return Contact.objects.get(is_active=True, supply_point=sp)
    except (SupplyPoint.DoesNotExist, Contact.DoesNotExist):
        return None
    except Contact.MultipleObjectsReturned:
        # this is weird, shouldn't be possible, but who knows.
        raise MultipleHSAException("More than one HSA found with id %s" % hsa_id)

def hsas_below(location):
    """
    Given an optional location, return all HSAs below that location.
    
    This method returns Contacts
    """
    hsas = Contact.objects.filter(role__code="hsa", is_active=True, 
                                  supply_point__active=True) 
    if location:
        # support up to 3 levels of parentage. this covers
        # hsa->facility-> district, which is all we allow you to select
        
        hsas = hsas.filter(Q(supply_point__location=location) | \
                           Q(supply_point__supplied_by__location=location) | \
                           Q(supply_point__supplied_by__supplied_by__location=location))
    return hsas
    
def hsa_supply_points_below(location):
    """
    Given an optional location, return all HSAs below that location.
    
    This method returns SupplyPoints
    """
    hsa_sps = SupplyPoint.objects.filter(type__code="hsa", active=True)
    if location:
        # support up to 3 levels of parentage. this covers
        # hsa->facility-> district, which is all we allow you to select
        hsa_sps = hsa_sps.filter(Q(location=location) | \
                                 Q(supplied_by__location=location) | \
                                 Q(supplied_by__supplied_by__location=location))
    return hsa_sps
    
    
def get_supervisors(supply_point):
    """
    Get all supervisors at a particular facility
    """
    return supply_point.active_contact_set.filter\
                (is_active=True, role__code__in=config.Roles.SUPERVISOR_ROLES)

def get_districts():
    return Location.objects.filter(type__slug=config.LocationCodes.DISTRICT)

def get_em_districts():
    # TODO, better abstraction of this
    return get_districts().filter(name__in=["Nkhotakota", "Nsanje", "Kasungu"])
    
def get_ept_districts():
    # TODO, better abstraction of this
    return get_districts().filter(name__in=["Machinga", "Nkhatabay", "Mulanje"])


def get_facilities():
    return Location.objects.filter(type__slug=config.LocationCodes.FACILITY)

def group_for_location(location):
    ''' This is specific for the Malawi case, separating HSAs into groups by district. '''
    if location.type.slug == config.LocationCodes.DISTRICT:
        for key in config.Groups.GROUPS:
            if location.name in config.Groups.GROUPS[key]:
                return key
    elif location.type.slug == config.LocationCodes.COUNTRY:
        return None # No country-level groups yet
    elif location.parent:
        return group_for_location(location.parent)
    else:
        return None

def facility_supply_points_below(location):
    facs = get_facility_supply_points()
    if location:
        # support up to 2 levels of parentage. this covers
        # facility-> district, which is all we allow you to select in this case
        facs = facs.filter(Q(location=location) | \
                           Q(location__parent_id=location.pk))
    return facs



def get_facility_supply_points():
    return SupplyPoint.objects.filter(type__code=config.SupplyPointCodes.FACILITY)