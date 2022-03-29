from __future__ import division
from contextlib import contextmanager

from rapidsms.models import Contact
from logistics.models import SupplyPoint, LogisticsProfile
from logistics.util import config
from logistics_project.apps.malawi.exceptions import MultipleHSAException, IdFormatException
from rapidsms.contrib.locations.models import Location
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from rapidsms.errors import MessageSendingError


@contextmanager
def swallow_errors(exc_type=MessageSendingError):
    try:
        yield
    except exc_type:
        pass


def get_backend_name_for_phone_number(phone_number):
    if phone_number.startswith('+2658'):
        return config.TNM_BACKEND_NAME
    elif phone_number.startswith('+2659'):
        return config.AIRTEL_BACKEND_NAME
    else:
        raise config.UnableToSelectBackend(
            "Unable to select backend for number starting with %s" % phone_number[:5]
        )


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


def get_facility(supply_point_code):
    """
    Attempts to get a Facility by code and returns None if unable to find it.
    """
    try:
        return SupplyPoint.objects.get(active=True, code=supply_point_code, type__code=config.SupplyPointCodes.FACILITY)
    except SupplyPoint.DoesNotExist:
        return None


def hsas_below(location):
    """
    Given an optional location, return all HSAs below that location.
    
    This method returns Contacts
    """
    hsas = Contact.objects.filter(role__code="hsa", is_active=True, 
                                  supply_point__active=True) 
    if location:
        if location.type_id == config.LocationCodes.HSA:
            hsas = hsas.filter(supply_point__location=location)
        elif location.type_id == config.LocationCodes.FACILITY:
            hsas = hsas.filter(supply_point__supplied_by__location=location)
        elif location.type_id == config.LocationCodes.DISTRICT:
            hsas = hsas.filter(supply_point__supplied_by__supplied_by__location=location)
        elif location.type_id == config.LocationCodes.ZONE:
            hsas = hsas.filter(supply_point__supplied_by__supplied_by__supplied_by__location=location)
        elif location.type_id == config.LocationCodes.COUNTRY:
            hsas = hsas.filter(supply_point__supplied_by__supplied_by__supplied_by__supplied_by__location=location)
        else:
            raise config.UnknownLocationCodeException(location.type_id)

    return hsas


def hsa_supply_points_below(location):
    """
    Given an optional location, return all HSAs below that location.
    
    This method returns SupplyPoints
    """
    hsa_sps = SupplyPoint.objects.filter(type__code="hsa", active=True, contact__is_active=True)
    if location:
        if location.type_id == config.LocationCodes.HSA:
            hsa_sps = hsa_sps.filter(location=location)
        elif location.type_id == config.LocationCodes.FACILITY:
            hsa_sps = hsa_sps.filter(supplied_by__location=location)
        elif location.type_id == config.LocationCodes.DISTRICT:
            hsa_sps = hsa_sps.filter(supplied_by__supplied_by__location=location)
        elif location.type_id == config.LocationCodes.ZONE:
            hsa_sps = hsa_sps.filter(supplied_by__supplied_by__supplied_by__location=location)
        elif location.type_id == config.LocationCodes.COUNTRY:
            hsa_sps = hsa_sps.filter(supplied_by__supplied_by__supplied_by__supplied_by__location=location)
        else:
            raise config.UnknownLocationCodeException(location.type_id)

    return hsa_sps
    
    
def _contact_set(supply_point, role):
    return supply_point.active_contact_set.filter\
                (is_active=True, role__code=role)


def get_supervisors(supply_point):
    """
    Retrieves the Contact objects for all contacts at the supply point that have
    supervisor roles.

    If supply_point is a facility, it returns all contacts at that facility who have
    roles that supervise HSAs.

    If supply_point is a district, it returns all contacts at that district who have
    roles that supervise facilities.

    Otherwise, an exception is raised.
    """
    if supply_point.type_id == config.SupplyPointCodes.FACILITY:
        role_codes = config.Roles.HSA_SUPERVISOR_ROLES
    elif supply_point.type_id == config.SupplyPointCodes.DISTRICT:
        role_codes = config.Roles.FACILITY_SUPERVISOR_ROLES
    else:
        raise config.BaseLevel.InvalidSupervisorLevelException(supply_point.type_id)

    return supply_point.active_contact_set.filter(role__code__in=role_codes)


def get_in_charge(supply_point):
    """
    Get all "in-charge" people at a particular facility
    """
    return _contact_set(supply_point, config.Roles.IN_CHARGE)
    
def get_imci_coordinators(supply_point):
    return _contact_set(supply_point, config.Roles.IMCI_COORDINATOR)
    
def get_district_pharmacists(supply_point):
    return _contact_set(supply_point, config.Roles.DISTRICT_PHARMACIST)
    
def get_districts(include_test=False):
    base = Location.objects.filter(type__slug=config.LocationCodes.DISTRICT, is_active=True)
    if not include_test:
        return remove_test_district(base)
    return base

def remove_test_district(qs):
    return qs.exclude(code='99')

def get_em_districts():
    # todo: everything is EM now so this method is no longer necessary
    return get_districts()
    
def get_ept_districts():
    # todo: everything is EM now so this method is no longer necessary
    return get_districts().none()

def get_facilities():
    return Location.objects.filter(type__slug=config.LocationCodes.FACILITY, is_active=True)


def facility_supply_points_below(location):
    facs = get_facility_supply_points()
    if location:
        if location.type_id == config.LocationCodes.FACILITY:
            facs = facs.filter(location=location)
        elif location.type_id == config.LocationCodes.DISTRICT:
            facs = facs.filter(supplied_by__location=location)
        elif location.type_id == config.LocationCodes.ZONE:
            facs = facs.filter(supplied_by__supplied_by__location=location)
        elif location.type_id == config.LocationCodes.COUNTRY:
            facs = facs.filter(supplied_by__supplied_by__supplied_by__location=location)
        else:
            raise config.UnknownLocationCodeException(location.type_id)

    return facs


def get_district_supply_points(include_test=False):
    base = SupplyPoint.objects.filter(active=True,
                                      type__code=config.SupplyPointCodes.DISTRICT)
    if not include_test:
        return remove_test_district(base)
    return base

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
    prof = get_user_profile(user)
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
        return list(get_districts(user.is_superuser).order_by('code'))

    profile = get_user_profile(user)
    loc = None
    locations = []

    if profile:
        # Add visible districts based on the user's organization

        if profile.organization:
            # If the user belongs to an organization, include the districts
            # managed by the organization.
            # We only allow settings districts as managed_supply_points for an
            # organization in the edit organization UI.
            locations.extend([d.location for d in profile.organization.managed_supply_points.all()])

        if profile.supply_point and profile.supply_point.location:
            loc = profile.supply_point.location
        elif profile.location:
            loc = profile.location

    if loc:
        # Add visible districts based on the user's profile

        if loc.type_id == config.LocationCodes.DISTRICT:
            locations.append(loc)
        elif loc.type_id == config.LocationCodes.ZONE:
            for l in Location.objects.filter(parent_id=loc.id, is_active=True):
                if l.code != '99' or user.is_superuser:
                    locations.append(l)
        elif loc.type_id == config.LocationCodes.COUNTRY:
            return list(get_districts(user.is_superuser).order_by('code'))

    return sorted(list(set(locations)), key=lambda loc: loc.code)


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


def deactivate_product(product):
    product.is_active = False
    product.save()
    managers = Contact.objects.filter(commodities__in=[product.pk])
    for c in managers:
        assert product in c.commodities.all()
        c.commodities.remove(product)


def get_managed_product_ids(supply_point, base_level):
    # Note that we .order_by('id') here because default ordering for Product objects
    # is by name, so if we didn't include this, django also tries to select name in the
    # raw query which is unnecessary
    return set(
        supply_point.commodities_stocked()
        .filter(type__base_level=base_level)
        .values_list('id', flat=True)
        .distinct()
        .order_by('id')
    )


def get_managed_products_for_contact(contact):
    if contact.supply_point and contact.supply_point.type_id == config.SupplyPointCodes.FACILITY:
        return contact.supply_point.commodities_stocked()
    else:
        return contact.commodities.all()


def get_supply_point_and_contacts(supply_point_code, base_level):
    """
    Given a supply point code, returns the list of contacts at that
    supply point and the supply point as a (list, SupplyPoint) tuple.

    If the supply point is not found, ([], None) is returned.
    """
    if base_level == config.BaseLevel.HSA:
        hsa = get_hsa(supply_point_code)
        if not hsa:
            return ([], None)

        return ([hsa], hsa.supply_point)
    elif base_level == config.BaseLevel.FACILITY:
        facility = get_facility(supply_point_code)
        if not facility:
            return ([], None)

        contacts = list(
            Contact.objects.filter(
                is_active=True,
                supply_point=facility,
                role__code__in=config.Roles.FACILITY_ONLY
            )
        )

        return (contacts, facility)
    else:
        raise config.BaseLevel.InvalidBaseLevelException(base_level)


def get_user_profile(user):
    if user and not user.is_anonymous():
        try:
            return LogisticsProfile.objects.get(user=user)
        except LogisticsProfile.DoesNotExist:
            return None


def get_or_create_user_profile(user):
    try:
        return LogisticsProfile.objects.get(user=user)
    except ObjectDoesNotExist:
        return LogisticsProfile.objects.create(user=user)


def filter_district_queryset_for_epi(district_qs):
    """
    Works on a queryset of SupplyPoint districts or Location districts.
    """
    return district_qs.filter(code__in=settings.EPI_DISTRICT_CODES)


def filter_district_list_for_epi(district_list):
    """
    Works on a list of SupplyPoint districts or Location districts.
    """
    return [d for d in district_list if d.code in settings.EPI_DISTRICT_CODES]


def filter_facility_supply_point_queryset_for_epi(facility_qs):
    """
    Works on a queryset of SupplyPoint facilities.
    """
    return facility_qs.filter(supplied_by__code__in=settings.EPI_DISTRICT_CODES)


def filter_facility_location_queryset_for_epi(facility_qs):
    """
    Works on a queryset of Location facilities.
    """
    return facility_qs.filter(supplypoint__supplied_by__code__in=settings.EPI_DISTRICT_CODES)
