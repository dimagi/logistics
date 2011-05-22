from rapidsms.contrib.locations.models import LocationType
from logistics.apps.logistics.models import SupplyPointType
from logistics.apps.logistics.models import ContactRole

HSA = "hsa"

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
    ADD_PRODUCT = "add_product"
    REMOVE_PRODUCT = "remove_product"
    ADD_USER = "add_user"
    REMOVE_USER = "remove_user"

def has_permissions_to(contact, operation):
    # one might want to use the responsibilities framework to manage
    # this but currently it seems strange that we'd have such tight
    # coupling between app logic and database logic, so it's here
    if not contact.is_active:
        return False
    if operation == Operations.REPORT_STOCK:
        return contact.role == ContactRole.objects.get(code=Roles.HSA)
    if operation == Operations.FILL_ORDER:
        return contact.role == ContactRole.objects.get(code=Roles.IN_CHARGE)
    if operation == Operations.MAKE_TRANSFER:
        return contact.role == ContactRole.objects.get(code=Roles.HSA)
    if operation == Operations.CONFIRM_TRANSFER:
        return contact.role == ContactRole.objects.get(code=Roles.HSA)
    if operation == Operations.REPORT_FOR_OTHERS:
        return contact.role in ContactRole.objects.filter(code__in=[Roles.HSA, Roles.IN_CHARGE])
    if operation == Operations.ADD_USER:
        return contact.role == ContactRole.objects.get(code=Roles.IN_CHARGE)
    if operation == Operations.REMOVE_USER:
        return contact.role == ContactRole.objects.get(code=Roles.IN_CHARGE)

    # TODO, fill this in more
    return True

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

class Messages(object):
    # some semblance of an attempt to start being consistent about this.
    
    # "register" keyword (hsa registration)
    HSA_HELP = "Sorry, I didn't understand. To register, send register [first name] [last name] [id] [facility]. Example: 'register john smith 1 1001'"
    
    # "manage" keyword (manger registration)
    MANAGER_HELP = "Sorry, I didn't understand. To register, send manage [first name] [last name] [role] [facility]. Example: 'manage john smith ic 1001'"

    # "leave" keyword 
    LEAVE_NOT_REGISTERED = "We do not have a record of your registration. Nothing was done."
    LEAVE_CONFIRM = "You have successfully left the cStock system. Goodbye!"
    
    # "soh" keyword (report stock on hand)
    SOH_HELP_MESSAGE = "To report stock on hand, send SOH [space] [product code] [space] [amount]"
    SUPERVISOR_SOH_NOTIFICATION = "%(hsa)s needs the following products: %(products)s. Respond 'ready %(hsa_id)s' when products are ready for pick up."
    SOH_ORDER_CONFIRM = "Thank you %(contact)s. The health center has been notified and you will receive a message when products are ready for pick up." 
    
    # "rec" keyword (receipts)
    RECEIPT_CONFIRM = 'Thank you, you reported receipts for %(products)s.'
    
    # "Ready" keyword 
    ORDERREADY_HELP_MESSAGE = "To confirm an order, type ready [space] [hsa id], for example: 'ready 100101'"
    APPROVAL_RESPONSE = "Thank you for confirming order for %(hsa)s. You confirmed ready: %(products)s"
    APPROVAL_NOTICE = "Dear %(hsa)s, your pending order is ready for pick up. The following products are ready: %(products)s"
    
    # "OS" keyword
    STOCKOUT_HELP = "To report stockouts, type os [space] [hsa id], for example: 'os 100101'"
    STOCKOUT_RESPONSE = "Thank you %(reporter)s. You have reported stockouts for the following products: %(products)s. The health center and district office have been notified."
    STOCKOUT_NOTICE = "Dear %(hsa)s, your pending order is stocked out at the health centre. Please work with the in-charge to resolve this issue in a timely manner."
    SUPERVISOR_STOCKOUT_NOTIFICATION = "%(contact)s has reported a stockout at %(supply_point)s. At least the following products are affected: %(products)s."
    
    # "eo" keyword (emergency orders)
    EMERGENCY_HELP = "To report an emergency, send 'eo [space] [product code] [space] [amount]'"
    SUPERVISOR_EMERGENCY_SOH_NOTIFICATION = "%(hsa)s needs emergency products: %(emergency_products)s, and additionally: %(normal_products)s. Respond 'ready %(hsa_id)s' or 'os %(hsa_id)s'"
    SUPERVISOR_EMERGENCY_SOH_NOTIFICATION_NO_ADDITIONAL = "%(hsa)s needs emergency products: %(emergency_products)s. Respond 'ready %(hsa_id)s' or 'os %(hsa_id)s'"
    
    # "Give" keyword (hsa to hsa transfers)
    TRANSFER_HELP_MESSAGE = "To report a stock transfer, type GIVE [receiving hsa id] [product code] [amount], for example: 'give 100101 zi 20'"
    TRANSFER_RESPONSE = "Thank you %(reporter)s. You have reported a transfer from %(giver)s to %(receiver)s of the following products: %(products)s"
    TRANSFER_CONFIRM = "Confirm receipt of %(products)s from %(giver)s? Please respond 'confirm'"
    
    # "confirm" keyword
    NO_PENDING_TRANSFERS = "Sorry, you don't have any pending transfers to confirm"
    CONFIRM_RESPONSE = "Thank you %(receiver)s. You have confirmed receipt of the following products: %(products)s"
    
    # "report" keyword (report for others)
    REPORT_HELP = "To report for someone else, type report [hsa id] [keyword] and the remainder of the report message. Valid keywords are: soh, rec, eo, give."
    BAD_REPORT_KEYWORD = "Sorry, %(keyword)s is not a valid keyword. Must be 'rec' or 'soh'"
    REPORT_SOH_RESPONSE = "%(hsa)s needs the following products: %(products)s. Type 'report %(hsa_id)s rec [prod code] [amount]' to report receipts for the HSA."
    REPORT_RECEIPT_RESPONSE = "Thank you %(reporter)s. You reported the following receipts for %(hsa)s: %(products)s"
    
    # product add/remove
    ADD_HELP_MESSAGE = "To add products you supply, send ADD [product codes]."
    REMOVE_HELP_MESSAGE = "To remove products you supply, send REMOVE [product codes]."
    ADD_SUCCESS_MESSAGE = "Thank you, you now supply: %(products)s"
    REMOVE_SUCCESS_MESSAGE = "Done. You now supply: %(products)s"
    UNKNOWN_CODE = "Sorry, no product matches code %(product)s.  Nothing done."
    
    # nag
    HSA_NAG_FIRST= "Dear %(hsa)s, your stock on hand report is due in %(days)d days. " + SOH_HELP_MESSAGE
    HSA_NAG_SECOND = "Dear %(hsa)s, you have not reported your stock on hand this month. " + SOH_HELP_MESSAGE
    HSA_NAG_THIRD = "Dear %(hsa)s, you must report your stock on hand.  Your supervisor has been notified. " + SOH_HELP_MESSAGE
    HSA_SUPERVISOR_NAG = "%(hsa)s has failed to report their stock on hand this month."

    # create user

    # boot user
    BOOT_HELP = "To remove a user from the system, type boot [hsa id]"
    BOOT_RESPONSE = "Done. %(contact)s has been removed from the cStock system."
    BOOT_ID_NOT_FOUND = "Couldn't find a record for user with id %(id)s. Nothing done."

    # Other  Messages (usually for error conditions)
    ALREADY_REGISTERED = "You are already registered. To change your information you must first text LEAVE"
    UNKNOWN_LOCATION = "Sorry, can't find the facility with CODE %(code)s. Please double check the facility code and try again."
    REGISTRATION_REQUIRED_MESSAGE = "Sorry, you have to be registered with the system to do that. For help, please contact your supervisor"
    UNSUPPORTED_OPERATION = "Sorry, your current role does not allow you to do that. For help, please contact your supervisor"
    UNKNOWN_HSA = "Cannot find hsa with id %(hsa_id)s. Please double check the id and try again."
    UNKNOWN_ROLE = "Sorry, I don't understand the role %(role)s. Valid roles are %(valid_roles)s"
    NO_SUPPLY_POINT_MESSAGE = "You are not associated with a facility. Please contact your district IMCI Focal Person for assistance."
    GENERIC_ERROR = "Sorry, something was wrong with that message. If you keep having trouble, contact your supervisor for help."
    NO_IN_CHARGE = "There is no HSA Supervisor registered for %(supply_point)s. Please contact your supervisor to resolve this."
    REGISTRATION_CONFIRM = "Congratulations %(contact_name)s, you have been registered for the cStock System. Your facility is %(sp_name)s and your role is: %(role)s"

