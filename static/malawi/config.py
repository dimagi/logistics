


HSA = "hsa"

class Roles(object):
    """
    Roles go here
    """
    HSA = HSA
    HSA_SUPERVISOR = "sh"
    IN_CHARGE = "ic"
    DISTRICT_SUPERVISOR = "ds"
    DISTRICT_PHARMACIST = "dp"
    IMCI_COORDINATOR = "im"
    ALL_ROLES = {
        HSA: "hsa",
        HSA_SUPERVISOR: "hsa supervisor",
        IN_CHARGE: "in charge",
        DISTRICT_SUPERVISOR: "district supervisor",
        DISTRICT_PHARMACIST: "district pharmacist",
        IMCI_COORDINATOR: "imci coordinator"
    }
    UNIQUE = []#DISTRICT_SUPERVISOR, IMCI_COORDINATOR]
    FACILITY_ONLY = [IN_CHARGE, HSA_SUPERVISOR]
    DISTRICT_ONLY = [DISTRICT_SUPERVISOR, DISTRICT_PHARMACIST, IMCI_COORDINATOR]
    SUPERVISOR_ROLES = [HSA_SUPERVISOR, IN_CHARGE]

class Operations(object):
    FILL_ORDER = "fill"
    MAKE_TRANSFER = "transfer"
    CONFIRM_TRANSFER = "confirm"
    REPORT_FOR_OTHERS = "report"
    REPORT_STOCK = "report_stock"
    REPORT_RECEIPT = "report_receipt"
    ADD_PRODUCT = "add_product"
    REMOVE_PRODUCT = "remove_product"
    ADD_USER = "add_user"
    REMOVE_USER = "remove_user"
    APPROVE_USER = "approve_user"
    REPORT_FRIDGE_MALFUNCTION = 'report_fridge_malfunction'
    ADVISE_FACILITY_TRANSFER = 'advise_facility_transfer'


class SupplyPointCodes(object):
    """
    These correspond to SupplyPointType.code
    """
    COUNTRY = "c"
    DISTRICT = "d"
    FACILITY = "hf"
    HSA = "hsa"
    
    ALL = {
        COUNTRY: "country",
        DISTRICT: "district",
        FACILITY: "facility",
        HSA: "hsa"
    }

class LocationCodes(object):
    """
    These correspond to LocationType.code
    """
    COUNTRY = "country"
    DISTRICT = "district"
    FACILITY = "facility"
    HSA = "hsa"
    
def has_permissions_to(contact, operation):
    # one might want to use the responsibilities framework to manage
    # this but currently it seems strange that we'd have such tight
    # coupling between app logic and database logic, so it's here
    from logistics.models import ContactRole
    if not contact.is_active:
        return False
    if operation == Operations.REPORT_STOCK:
        return contact.role == ContactRole.objects.get(code=Roles.HSA)
    if operation == Operations.REPORT_RECEIPT:
        return contact.role == ContactRole.objects.get(code=Roles.HSA)
    if operation in [Operations.ADD_PRODUCT, Operations.REMOVE_PRODUCT]:
        return contact.role == ContactRole.objects.get(code=Roles.HSA)
    if operation == Operations.FILL_ORDER:
        return contact.role in ContactRole.objects.filter(code__in=[Roles.HSA_SUPERVISOR, Roles.IN_CHARGE])
    if operation == Operations.MAKE_TRANSFER:
        return contact.role == ContactRole.objects.get(code=Roles.HSA)
    if operation == Operations.CONFIRM_TRANSFER:
        return contact.role == ContactRole.objects.get(code=Roles.HSA)
    if operation == Operations.REPORT_FOR_OTHERS:
        return True
#        return contact.role in ContactRole.objects.filter(code__in=[Roles.HSA, Roles.IN_CHARGE, Roles.HSA_SUPERVISOR])
    if operation == Operations.ADD_USER:
        return contact.role == ContactRole.objects.get(code=Roles.IN_CHARGE)
    if operation == Operations.REMOVE_USER:
        return contact.role == ContactRole.objects.get(code=Roles.IN_CHARGE)
    if operation == Operations.APPROVE_USER:
        return contact.role in ContactRole.objects.filter(code__in=[Roles.HSA_SUPERVISOR, Roles.IN_CHARGE])
    if operation == Operations.REPORT_FRIDGE_MALFUNCTION:
        return contact.role == ContactRole.objects.get(code=Roles.IN_CHARGE)
    if operation == Operations.ADVISE_FACILITY_TRANSFER:
        return contact.role == ContactRole.objects.get(code=Roles.DISTRICT_SUPERVISOR)
    # TODO, fill this in more
    return True

def hsa_supply_point_type():
    """
    The supply point type for HSAs
    """
    from logistics.models import SupplyPointType
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
    GROUPS = {EM: ("Nkhotakota", "Nsanje", "Kasungu", "Machinga", "Nkhatabay", "Mulanje"),
              EPT: ()}


class Messages(object):
    # some semblance of an attempt to start being consistent about this.
    
    # "register" keyword (hsa registration)
    HSA_HELP = "Sorry, I didn't understand. To register, send register [first name] [last name] [id] [facility]. Example: 'register john smith 1 1001'"
    REGISTRATION_CONFIRM = "Congratulations %(contact_name)s, you have been registered for the cStock System. Your facility is %(sp_name)s and your role is: %(role)s"
    REGISTRATION_DISTRICT_CONFIRM = "Congratulations %(contact_name)s, you have been registered for the cStock System. Your district is %(sp_name)s and your role is: %(role)s"

    # "manage" keyword (manger registration)
    MANAGER_HELP = "Sorry, I didn't understand. To register, send manage [first name] [last name] [role] [facility]. Example: 'manage john smith ic 1001'"
    ROLE_ALREADY_FILLED = "Sorry, there is already a user filling the %(role)s role."
    ROLE_WRONG_LEVEL = "Sorry, you cannot register as %(role)s on the %(level)s level."

    # "leave" keyword 
    LEAVE_NOT_REGISTERED = "We do not have a record of your registration. Nothing was done."
    LEAVE_CONFIRM = "You have successfully left the cStock system. Goodbye!"
    
    # "soh" keyword (report stock on hand)
    SOH_HELP_MESSAGE = "To report stock on hand, send SOH [space] [product code] [space] [amount]"
    SUPERVISOR_SOH_NOTIFICATION = "%(hsa)s needs the following products: %(products)s. Respond 'ready %(hsa_id)s' when products are ready for pick up."
    SUPERVISOR_SOH_NOTIFICATION_NOTHING_TO_DO = "%(hsa)s has submitted a stock report, but there is nothing to be filled. You do not need to do anything."
    SUPERVISOR_SOH_NOTIFICATION_WITH_STOCKOUTS = "%(hsa)s needs products: %(products)s. Some products are stocked out: %(stockedout_products)s. Respond 'ready %(hsa_id)s' when products are ready for pick up."
    SOH_ORDER_CONFIRM = "Thank you, you reported stock for %(products)s. The health center has been notified and you will receive a message when products are ready."
    SOH_ORDER_STOCKOUT_CONFIRM = "We have received your report of stock out of %(products)s and the health center has been notified. You will be notified when your products are available."
    SOH_ORDER_CONFIRM_NOTHING_TO_DO = "Thank you %(contact)s, you reported stock for %(products)s. Right now you do not need any products resupplied."
    
    # "rec" keyword (receipts)
    RECEIPT_CONFIRM = 'Thank you, you reported receipts for %(products)s.'
    RECEIPT_FROM_CONFIRM = 'Thank you, you reported receipts for %(products)s from %(supplier)s.'
    
    # "Ready" keyword 
    ORDERREADY_HELP_MESSAGE = "To confirm an order, type ready [space] [hsa id], for example: 'ready 100101'"
    APPROVAL_RESPONSE = "Thank you for confirming order for %(hsa)s."
    APPROVAL_NOTICE = "Dear %(hsa)s, your pending order is ready for pick up. If you have already collected your products please send a receipt."

    # "OS" keyword
    STOCKOUT_HELP = "To report stockouts, type os [space] [hsa id], for example: 'os 100101'"
    STOCKOUT_RESPONSE = "Thank you %(reporter)s. You have reported stockouts for the following products: %(products)s. Please contact the district office to resolve this issue."
    STOCKOUT_NOTICE = "Dear %(hsa)s, your pending order is stocked out at the health centre. The HSA supervisor will work with District to resolve this issue in a timely manner."
    SUPERVISOR_STOCKOUT_NOTIFICATION = "%(contact)s has reported a stockout at %(supply_point)s for at least these products: %(products)s. Work with the HSA Supervisor to resolve this issue."
    
    # "eo" keyword (emergency orders)
    EMERGENCY_HELP = "To report an emergency, send 'eo [space] [product code] [space] [amount]'"
    EMERGENCY_SOH = "We have received your emergency order for %(products)s and the health center has been notified. You will be notified when your products are available to pick up."
    EMERGENCY_STOCKOUT = "%(hsa)s is stocked out of and needs: %(stockouts)s, and additionally: %(normal_products)s. Respond 'ready %(hsa_id)s' or 'os %(hsa_id)s'"
    EMERGENCY_STOCKOUT_NO_ADDITIONAL = "%(hsa)s is stocked out of and needs: %(stockouts)s. Respond 'ready %(hsa_id)s' or 'os %(hsa_id)s'"
    SUPERVISOR_EMERGENCY_SOH_NOTIFICATION = "%(hsa)s needs emergency products %(emergency_products)s, also %(normal_products)s. Respond 'ready %(hsa_id)s' or 'os %(hsa_id)s'"
    SUPERVISOR_EMERGENCY_SOH_NOTIFICATION_NO_ADDITIONAL = "%(hsa)s needs emergency products: %(emergency_products)s. Respond 'ready %(hsa_id)s' or 'os %(hsa_id)s'"

    HF_UNABLE_RESTOCK_EO = "Thank you. You have reported that you are not able to resupply %(products)s. Please contact the District office to resolve this issue."
    HSA_UNABLE_RESTOCK_EO = "Dear %(hsa)s, the Health Center is not able to resupply %(products)s. The HSA Supervisor will work with the District to resolve this issue."
    DISTRICT_UNABLE_RESTOCK_EO = "%(contact)s reports %(supply_point)s is unable to resupply %(products)s in response to HSA EO. Work with the HSA Supervisor to resolve this issue."
    HSA_UNABLE_RESTOCK_ANYTHING = "Dear %(hsa)s, the Health Center is unable to resupply any of the products you need. The HSA Supervisor will work with the District to resolve this issue."
    DISTRICT_UNABLE_RESTOCK_STOCKOUT = "%(contact)s reports %(supply_point)s unable to resupply %(products)s in response to HSA stockout. Please work with the HSA Supervisor to resolve this issue."
    DISTRICT_UNABLE_RESTOCK_NORMAL = "%(contact)s has reported %(supply_point)s is unable to resupply any of the following %(products)s. Please work with the HSA Supervisor to resolve this issue."
    HSA_UNABLE_RESTOCK_STOCKOUT = HSA_UNABLE_RESTOCK_EO


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

    HSA_RECEIPT_NAG_FIRST = "Dear %(hsa)s, please pick up your products. If you've already done so, text 'rec [code] [amount] [code] [amount]...''"
    HSA_RECEIPT_NAG_SECOND = "Dear %(hsa)s, you must confirm receipt of your products. Please do so immediately. Your supervisor has been notified."
    HSA_RECEIPT_NAG_THIRD = "Dear %(hsa)s, you have still not confirmed receipt of your products. Your supervisor has been notified."
    HSA_RECEIPT_SUPERVISOR_NAG = "%(hsa)s has a fulfilled stock request they have not yet picked up."

    DISTRICT_NAG_EO = "%(pct)s%%%% of HSAs in your district have EOs that HC cannot resupply - visit the dashboard."
    DISTRICT_NAG_SO = "%(pct)s%%%% of HSAs in your district are stocked out of at least one product - visit the dashboard."

    # create user

    # boot user
    BOOT_HELP = "To remove a user from the system, type boot [hsa id]"
    BOOT_RESPONSE = "Done. %(contact)s has been removed from the cStock system."
    BOOT_ID_NOT_FOUND = "Couldn't find a record for user with id %(id)s. Nothing done."

    # approve user

    APPROVAL_WAITING = "Thank you for submitting your registration request, %(hsa)s. You will receive a message when your supervisor has approved your request."
    APPROVAL_REQUIRED = "You must be approved by your supervisor before doing that."
    APPROVAL_REQUEST = "%(hsa)s wants to register for the cStock system.  To approve them, text 'approve %(code)s'."
    APPROVAL_SUPERVISOR = "Successfully approved registration for %(hsa)s."
    APPROVAL_HSA = "Congratulations, your registration has been approved. Welcome to the cStock system, %(hsa)s."

    # Other  Messages (usually for error conditions)
    NO_PRODUCTS_MANAGED = "Please add the products you manage before reporting. Text 'add <code> <code>...' for all products you manage, then send your report again."
    ALREADY_REGISTERED = "You are already registered. To change your information you must first text LEAVE"
    UNKNOWN_LOCATION = "Sorry, can't find the facility with CODE %(code)s. Please double check the facility code and try again."
    REGISTRATION_REQUIRED_MESSAGE = "Sorry, you have to be registered with the system to do that. For help, please contact your supervisor"
    UNSUPPORTED_OPERATION = "Sorry, your current role does not allow you to do that. For help, please contact your supervisor"
    UNKNOWN_HSA = "Cannot find hsa with id %(hsa_id)s. Please double check the id and try again."
    UNKNOWN_ROLE = "Sorry, I don't understand the role %(role)s. Valid roles are %(valid_roles)s"
    NO_SUPPLY_POINT_MESSAGE = "You are not associated with a facility. Please contact your district IMCI Focal Person for assistance."
    GENERIC_ERROR = "Sorry, something was wrong with that message. If you keep having trouble, contact your supervisor for help."
    NO_IN_CHARGE = "There is no HSA Supervisor registered for %(supply_point)s. Please contact your supervisor to resolve this."
    TOO_MUCH_STOCK = 'Your %(keyword)s amount is too much and the message has been rejected. please resend your %(keyword)s message.'
    
    # messages originally in logistics.models.py
    SUPERVISOR_TITLE = 'your supervisor'
    GET_HELP_MESSAGE = "Please contact your %(supervisor)s for assistance." % {'supervisor' : SUPERVISOR_TITLE}
    NO_CODE_ERROR = "Stock report should contain at least one product code. " + \
                                "Please contact your %(supervisor)s for assistance." % {'supervisor' : SUPERVISOR_TITLE}
    NO_QUANTITY_ERROR ="Stock report should contain quantity of stock on hand. " + \
                                 "Please contact your %(supervisor)s for assistance." % {'supervisor': SUPERVISOR_TITLE}
    NO_SUPPLY_POINT_MESSAGE = "You are not associated with a facility. Please contact your district IMCI Focal Person for assistance."
    REGISTER_MESSAGE = "You must registered on cStock " + \
                       "before you can submit a stock report. " + \
                       "Please contact your %(supervisor)s." % {'supervisor' : SUPERVISOR_TITLE}
    SOH_HELP_MESSAGE = "To report stock on hand, send SOH [space] [product code] [space] [amount]"
    
    # reports
    NUMBER_OF_SUPPLY_POINTS = "Number of HSAs"
    
    # response to 'help'
    HELP_TEXT = "Text 'help stock' for help on the format of stock reports; " + \
                "'help codes' for a list of commodity codes; " + \
                "'help start' or 'help stop' to start and stop reminders."

    FRIDGE_BROKEN_NO_GAS = "no gas"
    FRIDGE_BROKEN_POWER_FAILURE = "power failure"
    FRIDGE_BROKEN_BREAKDOWN = "breakdown"

    FRIDGE_BROKEN_RESPONSE = ("Thank you. The district will be informed that your refrigerator is not working due "
        "to: %(reason)s")

    FRIDGE_BROKEN_NOTIFICATION = ("%(facility)s has a refrigerator malfunction due to: %(reason)s. Respond with "
        "'transfer %(facility)s [to facility] to advise the transfer of EPI products.")

    FRIDGE_HELP = "To report a refrigerator malfunction, please send 'rm [reason code]'"
    FRIDGE_HELP_REASON = ("'%(code)s' is not a valid reason code. Refrigerator malfunction reason code should be "
        "1:no gas, 2:power failure, 3:breakdown.")

    FRIDGE_MALFUNCTION_ALREADY_REPORTED = ("You already reported a refrigerator malfunction %(days)s days ago. "
        "If that malfunction has been fixed, please reply with 'rf', and then report the new malfunction with 'rm'")

    FRIDGE_NOT_REPORTED_BROKEN = "There is no open refrigerator malfunction reported at your health center."

    FRIDGE_CONFIRM_PRODUCTS_COLLECTED_FROM = ("Please reply with 'rc' to confirm you have collected your EPI "
        "products from %(facility)s")

    FRIDGE_CONFIRM_PRODUCTS_COLLECTED = "Please reply with 'rc' to confirm you have collected your EPI products"

    FRIDGE_NOT_REPORTED_FIXED = ("Your refrigerator has not been reported as fixed yet. If it has been "
        "fixed, please respond with 'rf'")

    FRIDGE_ALREADY_CONFIRMED_COLLECTED = "You have already confirmed that you have collected your EPI products."

    FRIDGE_CONFIRMATION_RESPONSE = "Thank you for confirming that you have collected your EPI products."

    ERROR_NO_FACILITY_ASSOCIATION = ("Your request cannot be processed because you are not associated with a "
        "health center. For help, please contact your supervisor.")

    ERROR_NO_DISTRICT_ASSOCIATION = ("Your request cannot be processed because you are not associated with a "
        "district. For help, please contact your supervisor.")

    FACILITY_TRANSFER_HELP = ("To advise a health center to transfer its EPI products to another health center, "
        "send 'transfer [health center from] [health center to]'")

    FACILITY_NOT_FOUND = ("Health center code '%(facility)s' is not valid. Please check the health center code "
        "and try again." )

    FACILITY_MUST_BE_DIFFERENT = ("You cannot choose the same health center as both the source and destination. "
        "Please try again.")

    FRIDGE_NOT_REPORTED_BROKEN_FOR_FACILITY = ("There is no open refrigerator malfunction reported at "
        "health center '%(facility)s'.")

    FRIDGE_REPORTED_BROKEN_FOR_FACILITY = ("There is an open refrigerator malfunction reported at "
        "health center '%(facility)s'. Please choose a different destination health center and try again.")

    TRANSFER_MESSAGE_TO_FACILITY = ("Please take your EPI stock to %(facility)s until your refrigerator is "
        "working again. Please notify cStock when it is working again by sending: 'rf'.")

    TRANSFER_RESPONSE_TO_DISTRICT = "Thank you, %(facility)s has been notified of the advised transfer."


class Alerts(object):
    
    HSA_NO_PRODUCTS = "%(hsa)s is registered but is not associated with any products"
    FACILITY_NO_SUPERVISOR = "No HSA supervisor or in-charge is registered for %(facility)s but there are HSAs registered there."

class TimeTrackerTypes:
    ORD_READY = 'ord-ready'
    READY_REC = 'ready-rec'
