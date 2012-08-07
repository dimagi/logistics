from rapidsms.models import Contact
from logistics.models import SupplyPoint, ProductStock
from logistics.util import config
from logistics_project.apps.malawi.exceptions import MultipleHSAException, IdFormatException
from rapidsms.contrib.locations.models import Location
from django.db.models.query_utils import Q
from django.conf import settings

def format_id(code, id):
    try:
        id_num = int(id)
        if id_num < 1 or id_num >= 100:
            raise IdFormatException("id must be a number between 1 and 99. %s is out of range" % id)
        return "%s%02d" % (code, id_num)
    except ValueError:
        raise IdFormatException("id must be a number between 1 and 99. %s is not a number" % id)
        
def pct(num, denom):
    return float(num) / (float(denom) or 1) * 100

def fmt_pct(num, denom):
    return "%.2f%%" % pct(num, denom)

def fmt_or_none(val, default_none="no data"):
    return "%.2f%%" % val if val is not None else default_none

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
        # support up to 4 levels of parentage. this covers
        # hsa-> facility-> district-> country, which is all we allow you to select
        
        hsas = hsas.filter(Q(supply_point__location=location) | \
                           Q(supply_point__supplied_by__location=location) | \
                           Q(supply_point__supplied_by__supplied_by__location=location) | \
                           Q(supply_point__supplied_by__supplied_by__supplied_by__location=location))
    return hsas
    
def hsa_supply_points_below(location):
    """
    Given an optional location, return all HSAs below that location.
    
    This method returns SupplyPoints
    """
    hsa_sps = SupplyPoint.objects.filter(type__code="hsa", active=True, contact__is_active=True)
    if location:
        # support up to 4 levels of parentage. this covers
        # hsa-> facility-> district-> country, which is all we allow you to select
        hsa_sps = hsa_sps.filter(Q(location=location) | \
                                 Q(supplied_by__location=location) | \
                                 Q(supplied_by__supplied_by__location=location) | \
                                 Q(supplied_by__supplied_by__supplied_by__location=location))
    return hsa_sps
    
    
def get_supervisors(supply_point):
    """
    Get all supervisors at a particular facility
    """
    return supply_point.active_contact_set.filter\
                (is_active=True, role__code__in=config.Roles.SUPERVISOR_ROLES)

def get_hsa_supervisors(supply_point):
    """
    Get all hsa supervisors at a particular facility
    """
    return supply_point.active_contact_set.filter\
                (is_active=True, role__code__in=config.Roles.HSA_SUPERVISOR)

def get_in_charge(supply_point):
    """
    Get all "in-charge" people at a particular facility
    """
    return supply_point.active_contact_set.filter\
                (is_active=True, role__code__in=config.Roles.IN_CHARGE)

def get_districts():
    return Location.objects.filter(type__slug=config.LocationCodes.DISTRICT, is_active=True)

def get_em_districts():
    # TODO, better abstraction of this
    return get_districts().filter(name__in=["Nkhotakota", "Nsanje", "Kasungu"])
    
def get_ept_districts():
    # TODO, better abstraction of this
    return get_districts().filter(name__in=["Machinga", "Nkhatabay", "Mulanje"])


def get_facilities():
    return Location.objects.filter(type__slug=config.LocationCodes.FACILITY, is_active=True)

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
        # support up to 3 levels of parentage. this covers
        # facility-> district--> country, which is all we allow you to select in this case
        facs = facs.filter(Q(location=location) | \
                           Q(supplied_by__location=location) | \
                           Q(supplied_by__supplied_by__location=location))
    return facs

def get_district_supply_points():
    return SupplyPoint.objects.filter(active=True, 
                                      type__code=config.SupplyPointCodes.DISTRICT)

def get_facility_supply_points():
    return SupplyPoint.objects.filter(active=True, 
                                      type__code=config.SupplyPointCodes.FACILITY)

def get_country_sp():
    return SupplyPoint.objects.get(code__iexact=settings.COUNTRY,
                                   type__code=config.SupplyPointCodes.COUNTRY)

class ConsumptionData(object):
    def __init__(self, product, sps):
        self.product = product
        self.sps = sps
        self.ps = ProductStock.objects.filter(supply_point__in=self.sps, product=self.product)

    def _consumption(self):
        if not self.ps: return [0]
        return [p.monthly_consumption for p in self.ps]

    @property
    def total_consumption(self):
        return sum(self._consumption())

    @property
    def average_consumption(self):
        q = self._consumption()
        if not q: return None
        return sum(q)/len(q)

    @property
    def total_stock(self):
        if not self.ps: return None
        return sum(filter(lambda x: x is not None, [p.quantity for p in self.ps]))

    @property
    def average_months_of_stock(self):
        mos = filter(lambda x: x is not None, [p.months_remaining for p in self.ps])
        return sum(mos)/len(mos) if len(mos) else None
