


HSA = "hsa"

class Languages(object):
    """
    These are used in ILSGateway
    """
    ENGLISH = "en"
    SWAHILI = "sw"
    DEFAULT = SWAHILI


DISTRICT_REG_DELIMITER = ":"

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
    REGISTER_HELP = "To register send reg <name> <msd code> or reg <name> at <district name>. Example:reg john patel d34002 or reg john patel at tandahimba"
    REGISTER_BAD_CODE = "I didn't recognize your msd code.  To register, send register <name> <msd code>. example: register Peter Juma d34002"
    REGISTER_UNKNOWN_CODE = "Sorry, can't find the location with MSD CODE %(msd_code)s"
    REGISTER_UNKNOWN_DISTRICT = "Sorry, can't find the location with the name %(name)s"
    REGISTRATION_CONFIRM = "Thank you for registering at %(sdp_name)s, %(msd_code)s, %(contact_name)s"
    REGISTRATION_CONFIRM_DISTRICT = "Thank you for registering at %(sdp_name)s, %(contact_name)s"

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

    # reminders
    REMINDER_STOCKONHAND = "Please send in your stock on hand information in the format 'soh <product> <amount> <product> <amount>...'"
    REMINDER_R_AND_R_FACILITY = "Have you sent in your R&R form yet for this quarter? Please reply \"submitted\" or \"not submitted\""
    REMINDER_R_AND_R_DISTRICT = "How many R&R forms have you submitted to MSD? Reply with 'submitted A <number of R&Rs submitted for group A> B <number of R&Rs submitted for group B>'"
    REMINDER_DELIVERY_FACILITY = "Did you receive your delivery yet? Please reply 'delivered <product> <amount> <product> <amount>...'"
    REMINDER_DELIVERY_DISTRICT = "Did you receive your delivery yet? Please reply 'delivered' or 'not delivered'"
    REMINDER_SUPERVISION = "Have you received supervision this month? Please reply 'supervision yes' or 'supervision no'"
    
    # "soh" keyword (report stock on hand)
    SOH_HELP_MESSAGE = "Please send in your stock on hand information in the format 'soh <product> <amount> <product> <amount>...'"
    SOH_BAD_FORMAT = "Sorry, invalid format. The message should be in the format 'soh <product> <amount> <product> <amount>...'"
    SOH_PARTIAL_CONFIRM = 'Thank you %(contact_name)s for reporting your stock on hand for %(facility_name)s.  Still missing %(product_list)s.'
    SOH_CONFIRM = "Thank you. Please send in your adjustments in the format 'la <product> +-<amount> +-<product> +-<amount>...'"
    SOH_ADJUSTMENTS_REMINDER = "Please send in your adjustments in the format 'la <product> +-<amount> +-<product> +-<amount>...'"

    # stock inquiry
    STOCK_INQUIRY_HELP_MESSAGE = "Please send in your stock on hand information in the format 'si <MSD product code> <amount>'"
    STOCK_INQUIRY_CONFIRM = 'Thank you, you reported you have %(quantity)s     %(product_name)s. If incorrect, please resend.'
    STOCK_INQUIRY_MESSAGE = "How much %(product_name)s (msd_code %(msd_code)s) do you have in stock?  Please respond 'si %(msd_code)s <amount>'"
    STOCK_INQUIRY_NOT_A_FACILITY_ERROR = "Can only initiate product inquiry for a single facility via SMS - %(location_name)s is a %(location_type)s"

    INVALID_PRODUCT_CODE = "Sorry, invalid product code %(product_code)s"

    #test handler
    TEST_HANDLER_HELP = "To test a reminder, send \"test [remindername] [msd code]\"; valid tests are soh, delivery, randr. Remember to setup your contact details!"
    TEST_HANDLER_BAD_CODE = "Invalid msd code %(code)s"
    TEST_HANDLER_CONFIRM = "Sent"

    # response to 'help'
    HELP_TEXT = "Haujasajiliwa,Tafadhali jisajili kwanza kabla ya kupata huduma," + \
                "Kusajili andika 'sajili<nafasi><jina lako><nafasi><msd code>'. " + \
                "Mfano 'sajili Peter Juma d34002'"

class Alerts(object):
    
    HSA_NO_PRODUCTS = "%(hsa)s is registered but is not associated with any products"
    FACILITY_NO_SUPERVISOR = "No HSA supervisor or in-charge is registered for %(facility)s but there are HSAs registered there."
