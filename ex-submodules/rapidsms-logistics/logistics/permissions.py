from rapidsms.contrib.locations.models import Location
from logistics.models import SupplyPoint


def user_can_view(user, location_or_sp, unconfigured_value=False):
    """
    Whether a user has permision to view a particular location or supply point.
    This is determined by walking up the parent chain and looking for their
    configured location. People can view anything above or below them, 
    but not on a different branch.
    
    If the user does not have a supply_point or location set in their profile
    then unconfigured_value is returned.
    """
    if location_or_sp == None: return unconfigured_value
    if isinstance(location_or_sp, Location):
        return user_can_view_loc(user, location_or_sp, unconfigured_value)
    elif isinstance(location_or_sp, SupplyPoint):
        return user_can_view_sp(user, location_or_sp, unconfigured_value)
    raise ValueError("Expected Location or SupplyPoint object but was %s" % \
                     type(location_or_sp))

# right now we compare locations by location and supply points by
# supply point. it seems silly to do it this way, but hopefully 
# the two models are always consistent with each other
def user_can_view_loc(user, location, unconfigured_value=False):
    prof = user.get_profile()
    if prof and prof.location and location:
        return prof.location == location \
            or prof.location.is_any_parent(location) \
            or location.is_any_parent(prof.location)
    else:
        return unconfigured_value
        
def user_can_view_sp(user, supply_point, unconfigured_value=False):
    prof = user.get_profile()
    if prof and prof.supply_point and supply_point:
        return prof.supply_point == supply_point \
            or prof.supply_point.is_any_supplier(supply_point) \
            or supply_point.is_any_supplier(prof.supply_point)
    else:
        return unconfigured_value
    