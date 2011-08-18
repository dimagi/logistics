


HSA = "hsa"

class Languages(object):
    """
    These are used in ILSGateway
    """
    ENGLISH = "en"
    SWAHILI = "sw"
    DEFAULT = SWAHILI




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
    RMO = "rmo"
    MOHSW = "mohsw"
    DMO = "dmo"
    MSD = "msd"
    ALL_ROLES = {
        IN_CHARGE: "Facility in-charge",
        DISTRICT_PHARMACIST: "District Pharmacist",
        RMO: "RMO",
        MOHSW: "MOHSW",
        DMO: "DMO",
        MSD: "MSD",
        DISTRICT_SUPERVISOR: "district supervisor",
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

class SupplyPointCodes(object):
    """
    These correspond to SupplyPointType.code
    """
    MOH = "moh"
    REGION = "region"
    DISTRICT = "district"
    FACILITY = "facility"
    
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

class Messages(object):
    # some semblance of an attempt to start being consistent about this.
    
    # "register" keyword (tz registration)
    REGISTER_HELP = "To register, send register <name> <msd code>. Example: register 'john patel d34002'"
    REGISTER_BAD_CODE = "I didn't recognize your msd code.  To register, send register <name> <msd code>. example: register Peter Juma d34002"
    REGISTER_UNKNOWN_CODE = "Sorry, can't find the location with MSD CODE %(msd_code)s"
    REGISTRATION_CONFIRM = "Thank you for registering at %(sdp_name)s, %(msd_code)s, %(contact_name)s"
    
    HELP_REGISTERED = 'Welcome to ILSGateway. Available commands are soh, delivered, not delivered, submitted, not submitted, language, sw, en, stop, supervision, la'
    HELP_UNREGISTERED = "To register, send register <name> <msd code>. Example: register 'john patel d34002'"
    
    # language keyword
    LANGUAGE_HELP = "To set your language, send LANGUAGE <CODE>"
    LANGUAGE_CONTACT_REQUIRED = "You must JOIN or IDENTIFY yourself before you can set your language preference."
    LANGUAGE_CONFIRM = "I will speak to you in %(language)s."
    LANGUAGE_UNKNOWN = 'Sorry, I don\'t speak "%(language)s".'
    
    # "stop" keyword
    STOP_CONFIRM = "You have requested to stop reminders to this number.  Send 'help' to this number for instructions on how to reactivate."
    
    # stockout
    STOCKOUT_HELP = "Please send in stockout reports in the form 'so <product>'"
    STOCKOUT_INVALID_CODES = "Sorry, invalid product codes %(codes)s"
    STOCKOUT_CONFIRM = 'Thank you %(contact_name)s for reporting stockouts of %(product_names)s for %(facility_name)s.'
    
    # l & a
    LOSS_ADJUST_HELP = "Please send in your adjustments in the format 'la <product> +-<amount> +-<product> +-<amount>...'"
    LOSS_ADJUST_BAD_FORMAT = "Sorry, invalid format.  The message should be in the format 'la <product> +-<amount> +-<product> +-<amount>..."
    LOSS_ADJUST_CONFIRM = "Thank you. Have you received supervision this month? Please reply 'supervision yes' or 'supervision no'"
    
    # supervision
    SUPERVISION_HELP = "Supervision reminders will come monthly, and you can respond 'supervision yes' if you have received supervision or 'supervision no' if you have not"
    SUPERVISION_CONFIRM_NO = 'You have reported that you have not yet received supervision this month.'
    SUPERVISION_CONFIRM_YES = 'Thank you for reporting that you have received supervision this month.'
    SUPERVISION_REMINDER = "Have you received supervision this month? Please reply 'supervision yes' or 'supervision no'"
    
    # yes
    YES_HELP = 'If you have submitted your R&R, respond \"submitted\".  If you have received your delivery, respond \"delivered\"'
    
    # not 
    NOT_HELP = "If you haven't submitted your R&R, respond \"not submitted\". If you haven't received your delivery, respond \"not delivered\""
    
    # not delivered
    NOT_DELIVERED_CONFIRM = "You have reported that you haven't yet received your delivery."

    # delivery
    DELIVERED_CONFIRM = "Thank you, you reported a delivery of %(reply_list)s. If incorrect, please resend."
    DELIVERY_BAD_FORMAT = "Sorry, invalid format.  The message should be in the format 'delivered product amount product amount'"
    DELIVERY_CONFIRM = "Thank you, you reported a delivery of %(reply_list)s. If incorrect, please resend."
    DELIVERY_PARTIAL_CONFIRM = "To record a delivery, respond with \"delivered product amount product amount...\""
    DELIVERY_REMINDER_FACILITY = "Did you receive your delivery yet? Please reply 'delivered <product> <amount> <product> <amount>...'"
    DELIVERY_REMINDER_DISTRICT = "Did you receive your delivery yet? Please reply 'delivered' or 'not delivered'"
    DELIVERY_CONFIRM_DISTRICT = "Thank you %(contact_name)s for reporting your delivery for %(facility_name)s"
    DELIVERY_LATE_DISTRICT = "Facility deliveries for group %(group_name)s (out of %(group_total)d): %(not_responded_count)d haven't responded and %(not_received_count)d have reported not receiving. See ilsgateway.com"
    #TODO This doesn't look right
    DELIVERY_CONFIRM_CHILDREN = "Sending alert to all facilities under %(district_name)s that they received delivery from from MSD"

    # not submitted
    NOT_SUBMITTED_CONFIRM = "You have reported that you haven't yet sent in your R&R."

    # submitted         
    SUBMITTED_CONFIRM = "Thank you %(contact_name)s for submitting your R and R form for %(sdp_name)s"
    SUBMITTED_REMINDER_FACILITY = "Have you sent in your R&R form yet for this quarter? Please reply \"submitted\" or \"not submitted\""
    SUBMITTED_REMINDER_DISTRICT= "How many R&R forms have you submitted to MSD? Reply with 'submitted A <number of R&Rs submitted for group A> B <number of R&Rs submitted for group B>'"

    # "soh" keyword (report stock on hand)
    SOH_HELP_MESSAGE = "Please send in your stock on hand information in the format 'soh <product> <amount> <product> <amount>...'"
    SOH_BAD_FORMAT = "Sorry, invalid format.  The message should be in the format 'soh <product> <amount> <product> <amount>'"
    SOH_PARTIAL_CONFIRM = 'Thank you %(contact_name)s for reporting your stock on hand for %(facility_name)s.  Still missing %(product_list)s.'
    SOH_CONFIRM = "Thank you. Please send in your adjustments in the format 'la <product> +-<amount> +-<product> +-<amount>...'"
    SOH_ADJUSTMENTS_REMINDER = "Please send in your adjustments in the format 'la <product> +-<amount> +-<product> +-<amount>...'"
    # old
    SUPERVISOR_SOH_NOTIFICATION = "%(hsa)s needs the following products: %(products)s. Respond 'ready %(hsa_id)s' when products are ready for pick up."
    SUPERVISOR_SOH_NOTIFICATION_NOTHING_TO_DO = "%(hsa)s has submitted a stock report, but there is nothing to be filled. You do not need to do anything."
    SUPERVISOR_SOH_NOTIFICATION_WITH_STOCKOUTS = "%(hsa)s needs products: %(products)s. Some products are stocked out: %(stockedout_products)s. Respond 'ready %(hsa_id)s' when products are ready for pick up."
    SOH_ORDER_CONFIRM = "Thank you, you reported stock for %(products)s. The health center has been notified and you will receive a message when products are ready."
    SOH_ORDER_STOCKOUT_CONFIRM = "We have received your report of stock out of %(products)s and the health center has been notified. You will be notified when your products are available."
    SOH_ORDER_CONFIRM_NOTHING_TO_DO = "Thank you %(contact)s, you reported stock for %(products)s. Right now you do not need any products resupplied."

    # stock inquiry
    STOCK_INQUIRY_HELP_MESSAGE = "Please send in your stock on hand information in the format 'si <MSD product code> <amount>'"
    STOCK_INQUIRY_CONFIRM = 'Thank you, you reported you have %(quantity)s     %(product_name)s. If incorrect, please resend.'
    STOCK_INQUIRY_MESSAGE = "How much %(product_name)s (msd_code %(msd_code)s) do you have in stock?  Please respond 'si %(msd_code)s <amount>'"
    STOCK_INQUIRY_PRODUCT_CODE_ERROR = "Invalid product code %(product_code)s"
    STOCK_INQUIRY_NOT_A_FACILITY_ERROR = "Can only initiate product inquiry for a single facility via SMS - %(location_name)s is a %(location_type)s"

    INVALID_PRODUCT_CODE = "Sorry, invalid product code %(code)s"

    #test handler
    TEST_HANDLER_HELP = "To test a reminder, send \"test [remindername] [msd code]\"; valid tests are soh, delivery, randr. Remember to setup your contact details!"
    TEST_HANDLER_BAD_CODE = "Invalid msd code %(code)s"
    TEST_HANDLER_CONFIRM = "Sent"

    # "register" keyword (hsa registration)
    HSA_HELP = "Sorry, I didn't understand. To register, send register [first name] [last name] [id] [facility]. Example: 'register john smith 1 1001'"
    
    REGISTRATION_DISTRICT_CONFIRM = "Congratulations %(contact_name)s, you have been registered for the cStock System. Your district is %(sp_name)s and your role is: %(role)s"

    # "manage" keyword (manger registration)
    MANAGER_HELP = "Sorry, I didn't understand. To register, send manage [first name] [last name] [role] [facility]. Example: 'manage john smith ic 1001'"
    ROLE_ALREADY_FILLED = "Sorry, there is already a user filling the %(role)s role."
    ROLE_WRONG_LEVEL = "Sorry, you cannot register as %(role)s on the %(level)s level."

    # "leave" keyword 
    LEAVE_NOT_REGISTERED = "We do not have a record of your registration. Nothing was done."
    LEAVE_CONFIRM = "You have successfully left the cStock system. Goodbye!"
    
    # "rec" keyword (receipts)
    RECEIPT_CONFIRM = 'Thank you, you reported receipts for %(products)s.'
    RECEIPT_FROM_CONFIRM = 'Thank you, you reported receipts for %(products)s from %(supplier)s.'
    
    # "Ready" keyword 
    ORDERREADY_HELP_MESSAGE = "To confirm an order, type ready [space] [hsa id], for example: 'ready 100101'"
    APPROVAL_RESPONSE = "Thank you for confirming order for %(hsa)s."
    APPROVAL_NOTICE = "Dear %(hsa)s, your pending order is ready for pick up."
    
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
    DISTRICT_UNABLE_RESTOCK_EO = "%(contact)s reports (supply_point) is unable to resupply %(products)s in response to HSA EO. Work with the HSA Supervisor to resolve this issue."
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
    ALREADY_REGISTERED = "You are already registered. To change your information you must first text LEAVE"
    UNKNOWN_LOCATION = "Sorry, can't find the facility with CODE %(code)s. Please double check the facility code and try again."
    REGISTRATION_REQUIRED_MESSAGE = "Sorry, you have to be registered with the system to do that. For help, please contact your supervisor"
    UNSUPPORTED_OPERATION = "Sorry, your current role does not allow you to do that. For help, please contact your supervisor"
    UNKNOWN_HSA = "Cannot find hsa with id %(hsa_id)s. Please double check the id and try again."
    UNKNOWN_ROLE = "Sorry, I don't understand the role %(role)s. Valid roles are %(valid_roles)s"
    NO_SUPPLY_POINT_MESSAGE = "You are not associated with a facility. Please contact your district IMCI Focal Person for assistance."
    GENERIC_ERROR = "Sorry, something was wrong with that message. If you keep having trouble, contact your supervisor for help."
    NO_IN_CHARGE = "There is no HSA Supervisor registered for %(supply_point)s. Please contact your supervisor to resolve this."
    
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
    HELP_TEXT = "Haujasajiliwa,Tafadhali jisajili kwanza kabla ya kupata huduma," + \
                "Kusajili andika 'sajili<nafasi><jina lako><nafasi><msd code>'. " + \
                "Mfano 'sajili Peter Juma d34002'"

class Alerts(object):
    
    HSA_NO_PRODUCTS = "%(hsa)s is registered but is not associated with any products"
    FACILITY_NO_SUPERVISOR = "No HSA supervisor or in-charge is registered for %(facility)s but there are HSAs registered there."
