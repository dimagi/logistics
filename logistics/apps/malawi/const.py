from logistics.apps.logistics.models import SupplyPointType
from rapidsms.contrib.locations.models import LocationType


def hsa_supply_point_type():
    """
    The supply point type for HSAs
    """
    return SupplyPointType.objects.get(pk="hsa")

def hsa_location_type():
    """
    The location type for HSAs
    """
    return LocationType.objects.get(slug="hsa")