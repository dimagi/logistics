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
    IMCI_COORDINATOR = "im"
    ALL_ROLES = {
        HSA: "hsa",
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
    REPORT_STOCK = "report_stock"
    
class Messages(object):
    # some semblance of an attempt to start being consistent about this.
    ALREADY_REGISTERED = "You are already registered. To change your information you must first text LEAVE"
    UNKNOWN_LOCATION = "Sorry, can't find the location with CODE %(code)s. Please double check the location code and try again."
    REGISTRATION_REQUIRED_MESSAGE = "Sorry, you have to be registered with the system to do that. For help, please contact your supervisor"
    UNSUPPORTED_OPERATION = "Sorry, your current role does not allow you to do that. For help, please contact your supervisor"
    UNKNOWN_HSA = "Cannot find hsa with id %(hsa_id)s. Please double check the id and try again."
    UNKNOWN_ROLE = "Sorry, I don't understand the role %(role)s. Valid roles are %(valid_roles)s"
    NO_SUPPLY_POINT_MESSAGE = "You are not associated with a facility. Please contact your district administrator for assistance."
    GENERIC_ERROR = "Sorry, something was wrong with that message. If you keep having trouble contact your supervisor for help."
    NO_IN_CHARGE = "There is no in-charge registered for %(supply_point)s. Please contact your supervisor to resolve this."
    REGISTRATION_CONFIRM = "Congratulations %(contact_name)s, you have been registered for the cStock System. Your facility is %(sp_name)s and your role is: %(role)s"
    # orderready
    ORDERREADY_HELP_MESSAGE = "To confirm an order type ready [space] [hsa id], for example: 'ready 100101'"
    APPROVAL_RESPONSE = "Thank you for confirming order for %(hsa)s. You approved: %(products)s"
    APPROVAL_NOTICE = "Dear %(hsa)s, your pending order has been approved. The following supplies are ready: %(products)s"
    # order stockout
    STOCKOUT_HELP = "To report stockouts type os [space] [hsa id], for example: 'os 100101'"
    STOCKOUT_RESPONSE = "Thank you %(reporter)s. You have reported stockouts for the following products: %(products)s. The district office has been notified."
    STOCKOUT_NOTICE = "Dear %(hsa)s, your pending order is stocked out at the facility. Please work with the in-charge to resolve this issue in a timely manner."
    SUPERVISOR_STOCKOUT_NOTIFICATION = "%(contact)s has reported a stockout at %(supply_point)s. At least the following products are affected: %(products)s."
    # partial order availability
    PARTIAL_FILL_HELP = "To partially fill an order type partial [space] [hsa id], for example: 'partial 100101'"
    PARTIAL_FILL_RESPONSE = "Thank you for partially confirming order for %(hsa)s. You approved some of: %(products)s"
    PARTIAL_FILL_NOTICE = "Dear %(hsa)s, your pending is now ready to be partially filled. Not all products were available but some are ready."
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
    SOH_ORDER_CONFIRM = "Thank you %(contact)s. The health center in charge has been notified and you will receive an alert when supplies are ready." 
    # emergency
    EMERGENCY_HELP = "To report an emergency, send 'eo [space] [product code] [space] [amount]'"
    SUPERVISOR_EMERGENCY_SOH_NOTIFICATION = "%(hsa)s needs emergency products: %(emergency_products)s, and additionally: %(normal_products)s. Respond 'ready %(hsa_id)s' or 'os %(hsa_id)s'"
    # report
    REPORT_HELP = "To report stock for someone use: report [hsa id] soh [prod code] [amount]. To report receipts use: report [hsa id] soh [prod code] [amount]"
    BAD_REPORT_KEYWORD = "Sorry, %(keyword)s is not a valid keyword. Must be 'rec' or 'soh'"
    REPORT_SOH_RESPONSE = "%(hsa)s needs the following products: %(products)s. Use 'report %(hsa_id)s rec [prod code] [amount]' to report receipts for the HSA."
    REPORT_RECEIPT_RESPONSE = "Thank you %(reporter)s. You reported the following receipts for %(hsa)s: %(products)s"
    # registration
    HSA_HELP = "Sorry, I didn't understand. To register, send register <name> <id> <parent facility>. Example: 'register john 1 1001'"
    # manager registration
    MANAGER_HELP = "Sorry, I didn't understand. To register, send manage <name> <role> <parent facility>. Example: 'manage john ic 1001'"
    # leave
    LEAVE_NOT_REGISTERED = "We do not have a record of your registration. Nothing was done."
    LEAVE_CONFIRM = "You have successfully left the cStock system. Goodbye!"
    #nag
    HSA_NAG_FIRST = "Dear %(hsa)s, you have not reported your stock on hand this month. " + SOH_HELP_MESSAGE
    HSA_NAG_SECOND = "Dear %(hsa)s, you must report your stock on hand. " + SOH_HELP_MESSAGE
    HSA_NAG_THIRD = "Dear %(hsa)s, you must report your stock on hand.  Your supervisor has been notified. " + SOH_HELP_MESSAGE
    HSA_SUPERVISOR_NAG = "%(hsa)s has failed to report their stock on hand this month."



