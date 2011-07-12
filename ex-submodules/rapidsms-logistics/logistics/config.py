########################
# MODULE CONFIG
########################
from rapidsms.conf import settings
mlog_app = getattr(settings,'MESSAGELOG_APP','rapidsms.contrib.messagelog')
# rl: not sure why i have to specifically list submodules...
messagelog = __import__(mlog_app, fromlist = ['models'])

########################
# CONSTANTS CONFIG
########################
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
    REPORT_RECEIPT = "report_receipt"
    ADD_PRODUCT = "add_product"
    REMOVE_PRODUCT = "remove_product"

def has_permissions_to(contact, operation):
    # one might want to use the responsibilities framework to manage
    # this but currently it seems strange that we'd have such tight
    # coupling between app logic and database logic, so it's here
    from logistics.apps.logistics.models import ContactRole
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
        return contact.role == ContactRole.objects.get(code=Roles.IN_CHARGE)
    # TODO, fill this in more
    return True


def hsa_supply_point_type():
    """
    The supply point type for HSAs
    """
    from logistics.apps.logistics.models import SupplyPointType
    return SupplyPointType.objects.get(pk=HSA)

def hsa_location_type():
    """
    The location type for HSAs
    """
    from rapidsms.contrib.locations.models import LocationType
    return LocationType.objects.get(slug=HSA)

class Groups(object):
    EPT = "ept"
    EM = "em"
    GROUPS = {EM: ("Nkhotakota", "Nsanje", "Kasungu"),
              EPT: ("Machinga", "Nkhatabay", "Mulanje")}

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
    SOH_ORDER_CONFIRM = "Thank you, you reported stock for %(products)s. The health center has been notified and you will get a message when products are ready." 
    # "rec" keyword (receipts)
    RECEIPT_CONFIRM = 'Thank you, you reported receipts for %(products)s.'
    RECEIPT_FROM_CONFIRM = 'Thank you, you reported receipts for %(products)s from %(supplier)s.'
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
    # "Give" keyword (hsa to hsa transfers)
    TRANSFER_HELP_MESSAGE = "To report a stock transfer, type GIVE [receiving hsa id] [product code] [amount], for example: 'give 100101 zi 20'"
    TRANSFER_RESPONSE = "Thank you %(giver)s. You have transferred to %(receiver)s the following products: %(products)s"
    TRANSFER_CONFIRM = "Confirm receipt of %(products)s from %(giver)s? Please respond 'confirm'"
    # "confirm" keyword
    NO_PENDING_TRANSFERS = "Sorry, you don't have any pending transfers to confirm"
    CONFIRM_RESPONSE = "Thank you %(receiver)s. You have confirmed receipt of the following products: %(products)s"
    # "report" keyword (report for others)
    REPORT_HELP = "To report stock for someone else, type report [hsa id] soh [prod code] [amount]. To report receipts, type report [hsa id] rec [prod code] [amount]"
    BAD_REPORT_KEYWORD = "Sorry, %(keyword)s is not a valid keyword. Must be 'rec' or 'soh'"
    REPORT_SOH_RESPONSE = "%(hsa)s needs the following products: %(products)s. Type 'report %(hsa_id)s rec [prod code] [amount]' to report receipts for the HSA."
    REPORT_RECEIPT_RESPONSE = "Thank you %(reporter)s. You reported the following receipts for %(hsa)s: %(products)s"
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
    # product add/remove
    ADD_HELP_MESSAGE = "To add products you supply, send ADD [product codes]."
    REMOVE_HELP_MESSAGE = "To remove products you supply, send REMOVE [product codes]."
    ADD_FAILURE_MESSAGE = "You are already supplying: %(products)s. Nothing done."
    REMOVE_FAILURE_MESSAGE = "You are not currently supplying: %(products)s. Nothing done."
    ADD_SUCCESS_MESSAGE = "Thank you, you are now supplying: %(products)s"
    REMOVE_SUCCESS_MESSAGE = "Thank you, you no longer supply: %(products)s"
    UNKNOWN_CODE = "Sorry, no product matches code %(product)s.  Nothing done."
    #nag
    HSA_NAG_FIRST = "Dear %(hsa)s, you have not reported your stock on hand this month. " + SOH_HELP_MESSAGE
    HSA_NAG_SECOND = "Dear %(hsa)s, you must report your stock on hand. " + SOH_HELP_MESSAGE
    HSA_NAG_THIRD = "Dear %(hsa)s, you must report your stock on hand.  Your supervisor has been notified. " + SOH_HELP_MESSAGE
    HSA_SUPERVISOR_NAG = "%(hsa)s has failed to report their stock on hand this month."

    # partial order availability
    PARTIAL_FILL_HELP = "To partially fill an order type partial [space] [hsa id], for example: 'partial 100101'"
    PARTIAL_FILL_RESPONSE = "Thank you for partially confirming order for %(hsa)s. You approved some of: %(products)s"
    PARTIAL_FILL_NOTICE = "Dear %(hsa)s, your pending is now ready to be partially filled. Not all products were available but some are ready."

    # messages originally in logistics.models.py
    SUPERVISOR_TITLE = 'your supervisor'
    GET_HELP_MESSAGE = "Please contact your %(supervisor)s for assistance." % {'supervisor' : SUPERVISOR_TITLE}
    NO_CODE_ERROR = "Stock report should contain at least one product code. " + \
                                "Please contact your %(supervisor)s for assistance." % {'supervisor' : SUPERVISOR_TITLE}
    NO_QUANTITY_ERROR ="Stock report should contain quantity of stock on hand. " + \
                                 "Please contact your %(supervisor)s for assistance." % {'supervisor': SUPERVISOR_TITLE}
    NO_SUPPLY_POINT_MESSAGE = "You are not associated with a facility. Please contact your district IMCI Focal Person for assistance."
    REGISTER_MESSAGE = "You must be registered on this system " + \
                       "before you can submit a stock report. " + \
                       "Please contact your %(supervisor)s." % {'supervisor' : SUPERVISOR_TITLE}
    SOH_HELP_MESSAGE = "To report stock on hand, send SOH [space] [product code] [space] [amount]"

