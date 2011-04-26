from logistics.apps.logistics.models import SupplyPointType
from rapidsms.contrib.locations.models import LocationType

HSA = "hsa"


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

class Roles(object):
    """
    Roles go here
    """
    HSA = HSA
    SENIOR_HSA = "sh"
    IN_CHARGE = "ic"
    CLUSTER_SUPERVISOR = "cs"
    DISTRICT_SUPERVISOR = "ds"
    DISTRICT_PHARMACIST = "dp"
    IMCI_COORDINATOR = "ic"
    ALL_ROLES = {
        HSA: "health surveillance assistant",
        SENIOR_HSA: "senior hsa",
        IN_CHARGE: "in charge",
        CLUSTER_SUPERVISOR: "cluster supervisor",
        DISTRICT_SUPERVISOR: "district supervisor",
        DISTRICT_PHARMACIST: "district pharmacist",
        IMCI_COORDINATOR: "imci coordinator"
    }

class Operations(object):
    FILL_ORDER = "fill"
    MAKE_TRANSFER = "transfer"
    CONFIRM_TRANSFER = "confirm"
    REPORT_FOR_OTHERS = "report"
    
class Messages(object):
    # some semblance of an attempt to start being consistent about this.
    REGISTRATION_REQUIRED_MESSAGE = "Sorry, you have to be registered with the system to do that. For help, please contact your supervisor"
    UNSUPPORTED_OPERATION = "Sorry, your current role does not allow you to do that. For help, please contact your supervisor"
    UNKNOWN_HSA = "Cannot find hsa with id %(hsa_id)s. Please double check the id and try again."
    NO_SUPPLY_POINT_MESSAGE = "You are not associated with a facility. Please contact your district administrator for assistance."
    GENERIC_ERROR = "Sorry, something was wrong with that message. If you keep having trouble contact your supervisor for help."
    # orderready
    ORDERREADY_HELP_MESSAGE = "To confirm an order type ready [space] [hsa id], for example: 'ready 100101'"
    APPROVAL_RESPONSE = "Thank you for confirming order for %(hsa)s. You approved: %(products)s"
    APPROVAL_NOTICE = "Dear %(hsa)s, your pending order has been approved. The following supplies are ready: %(products)s"
    # order stockout
    STOCKOUT_HELP = "To report stockouts type os [space] [hsa id], for example: 'os 100101'"
    STOCKOUT_RESPONSE = "Thank you %(reporter)s. You have reported stockouts for the following products: %(products)s. The district office has been notified."
    STOCKOUT_NOTICE = "Dear %(hsa)s, your pending order is stocked out at the facility. Please work with the in-charge to resolve this issue in a timely manner."
    # transfers
    TRANSFER_HELP_MESSAGE = "To report a stock transfer type GIVE [hsa id] [product code] [amount], for example: 'give 100101 zi 20'"
    TRANSFER_RESPONSE = "Thank you %(giver)s. You have transfered %(receiver)s the following products: %(products)s"
    TRANSFER_CONFIRM = "Confirm receipt of %(products)s from %(giver)s? Please respond 'confirm'"
    # transfer confirm
    NO_PENDING_TRANSFERS = "Sorry, you don't have any pending transfers to confirm"
    CONFIRM_RESPONSE = "Thank you %(receiver)s. You have confirmed receipt of the following products: %(products)s"
    # soh
    SOH_HELP_MESSAGE = "To report stock on hand, send SOH [space] [product code] [space] [amount]"
    SUPERVISOR_SOH_NOTIFICATION = "%(hsa)s needs the following supplies: %(supplies)s. Respond 'ready %(hsa_id)s' when supplies are ready"

    # report
    REPORT_HELP = "To report stock for someone use: report [hsa id] soh [prod code] [amount]. To report receipts use: report [hsa id] soh [prod code] [amount]"
    BAD_REPORT_KEYWORD = "Sorry, %(keyword)s is not a valid keyword. Must be 'rec' or 'soh'"
    REPORT_SOH_RESPONSE = "%(hsa)s needs the following products: %(products)s. Use 'report %(hsa_id)s rec [prod code] [amount]' to report receipts for the HSA."
    REPORT_RECEIPT_RESPONSE = "Thank you %(reporter)s. You reported the following receipts for %(hsa)s: %(products)s"
    # registration
    HSA_HELP = "Sorry, I didn't understand. To register, send register <name> <id> <parent facility>. Example: 'register john 1 1001'"
    # manager registration
    MANAGER_HELP = "Sorry, I didn't understand. To register, send manage <name> <role> <parent facility>. Example: 'manage john ic 1001'"

