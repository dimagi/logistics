from logistics.apps.logistics.models import SupplyPointType
from rapidsms.contrib.locations.models import LocationType

HSA = "hsa"

ROLE_HSA = HSA
ROLE_SENIOR_HSA = "senior_hsa"
ROLE_IN_CHARGE = "in_charge"
ROLE_CLUSTER_SUPERVISOR = "cluster_supervisor"
ROLE_DISTRICT_SUPERVISOR = "district_supervisor"
ROLE_DISTRICT_PHARMACIST = "district_pharmacist"
ROLE_IMCI_COORDINATOR = "imci_coordinator"

ROLES = {
    ROLE_HSA: "health surveillance assistant",
    ROLE_SENIOR_HSA: "senior hsa",
    ROLE_IN_CHARGE: "in charge",
    ROLE_CLUSTER_SUPERVISOR: "cluster supervisor",
    ROLE_DISTRICT_SUPERVISOR: "district supervisor",
    ROLE_DISTRICT_PHARMACIST: "district pharmacist",
    ROLE_IMCI_COORDINATOR: "imci coordinator"
}

REPORT_SOH = "soh"
REPORT_REC = "rec"

REPORTS = {
    REPORT_SOH: "stock on hand",
    REPORT_REC: "stock received"
}
def hsa_supply_point_type():
    """
    The supply point type for HSAs
    """
    return SupplyPointType.objects.get(pk=HSA)

def hsa_location_type():
    """
    The location type for HSAs
    """
    return LocationType.objects.get(slug=HSA)