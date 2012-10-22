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
    if denom == 0:
        assert num == 0
        return 0
    return float(num) / (float(denom) or 1) * 100

def fmt_pct(num, denom):
    return "%.0f%%" % pct(num, denom)

def fmt_or_none(val, default_none="no data", percent=True):
    base = "%.0f%%" if percent else "%.0f" 
    return base % val if val is not None else default_none

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
    
    
def _contact_set(supply_point, role):
    return supply_point.active_contact_set.filter\
                (is_active=True, role__code=role)
    
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
    return _contact_set(supply_point, config.Roles.HSA_SUPERVISOR)

def get_in_charge(supply_point):
    """
    Get all "in-charge" people at a particular facility
    """
    return _contact_set(supply_point, config.Roles.IN_CHARGE)
    
def get_imci_coordinators(supply_point):
    return _contact_set(supply_point, config.Roles.IMCI_COORDINATOR)
    
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

def is_country(supply_point):
    return supply_point.type.code == config.SupplyPointCodes.COUNTRY
        
def is_district(supply_point):
    return supply_point.type.code == config.SupplyPointCodes.DISTRICT
        
def is_facility(supply_point):
    return supply_point.type.code == config.SupplyPointCodes.FACILITY
        
def get_default_supply_point(user):
    prof = user.get_profile()
    if prof and prof.supply_point:
        return prof.supply_point
    elif prof and prof.location:
        try:
            return SupplyPoint.objects.get(location=prof.location)
        except SupplyPoint.DoesNotExist:
            pass
    return get_country_sp()

def get_view_level(user):
    """
    Is user affiliated with national or a district
    """
    if user.is_superuser:
        return 'national'

    for group in user.groups.all():
        if group.name == 'national':
            return 'national'
    return 'district'

def get_visible_districts(user):
    """
    Given a user, what districts can they see
    """
    if get_view_level(user) == 'national':
        return get_districts()

    prof = user.get_profile()
    loc = None
    locations = []
    # add managed districts for the organization
    if prof and prof.organization:
        locations = [d.location for d in prof.organization.managed_supply_points.all()]
    # check user's assigned district
    if prof and prof.supply_point and prof.supply_point.location:
        loc = prof.supply_point.location
    # in case location is set, but not supply_point
    elif prof and prof.location:
        loc = prof.location
    if loc and loc.type.slug == config.LocationCodes.DISTRICT:
        for l in Location.objects.filter(pk=loc.pk):
            locations.append(l)
    elif loc:
        # support one level deep, assuming that this is national or nothing
        for l in Location.objects.filter(parent_id=loc.id, is_active=True,\
                type__slug=config.LocationCodes.DISTRICT):
            locations.append(l)
    return locations

def get_visible_facilities(user):
    """
    Given a user, what facilities can they see
    """
    if get_view_level(user) == 'national':
        return get_facilities()

    visible_districts = get_visible_districts(user)
    vd_ids = [d.id for d in visible_districts]
    locations = Location.objects.filter(parent_id__in=vd_ids, 
                                        is_active=True).order_by('parent_id')
    return locations

def get_visible_hsas(user):
    """
    Given a user, what facilities can they see
    """
    if get_view_level(user) == 'national':
        return get_facilities()

    visible_facilities = get_visible_facilities(user)
    vf_ids = []
    for vf in visible_facilities:
        vf_ids.append(vf.id)
    locations = Location.objects.filter(parent_id__in=vf_ids, is_active=True)
    return locations

def get_all_visible_locations(user):
    """
    Given a user, what locations can they see
    """
    locations = [get_country_sp().location]
    for sp in get_visible_districts(user):
        locations.append(sp)
    for sp in get_visible_facilities(user):
        locations.append(sp)
    return locations

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
