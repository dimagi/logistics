from logistics.apps.malawi.const import hsa_supply_point_type
from logistics.apps.logistics.models import SupplyPoint
from rapidsms.models import Contact
from logistics.apps.malawi.exceptions import MultipleHSAException


def get_hsa(hsa_id):
    """
    Attempt to get an HSA by code, return None if unable to find them.
    """
    # in the future we should do some massaging of this code as well
    # to catch things like o's -> 0's and such.
    try:
        sp = SupplyPoint.objects.get(code=hsa_id, type=hsa_supply_point_type())
        return Contact.objects.get(supply_point=sp)
    except (SupplyPoint.DoesNotExist, Contact.DoesNotExist):
        return None
    except Contact.MultipleObjectsReturned:
        # this is weird, shouldn't be possible, but who knows.
        raise MultipleHSAException("More than one HSA found with id %s" % hsa_id)