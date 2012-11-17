########################
# MODULE CONFIG
########################
from rapidsms.conf import settings
# annoyingly, settings.x throws a valueerror when x is not set
if hasattr(settings,'MESSAGELOG_APP'):
    # rl: not sure why i have to specifically list submodules...
    messagelog = __import__(settings.MESSAGELOG_APP, fromlist = ['models'])
else:
    import rapidsms.contrib.messagelog as messagelog

class Roles(object):
    """
    Roles go here
    """
    IN_CHARGE = "incharge"
    PHARMACIST = "pharmacist"
    NURSE = "nurse"
    LABORATORY_STAFF = "lab"
    OTHER = "other"
    ALL_ROLES = {
        IN_CHARGE: "In Charge",
        PHARMACIST: "Pharmacist",
        NURSE: "Nurse",
        LABORATORY_STAFF: "Laboratory Staff",
        OTHER: "Other"
    }

class Responsibilities(object):
    """
    Roles go here
    """
    STOCK_ON_HAND_RESPONSIBILITY = 'reporter'
    REPORTEE_RESPONSIBILITY = 'reportee'
    ALL = {
        STOCK_ON_HAND_RESPONSIBILITY: 'report stock on hand',
        REPORTEE_RESPONSIBILITY: 'respond to reports of stock on hand'
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
    ADD_USER = "add_user"
    REMOVE_USER = "remove_user"

class SupplyPointCodes(object):
    """
    These correspond to SupplyPointType.code
    """
    REGIONAL_MEDICAL_STORE = "RMS"
    DISTRICT_HOSPITAL = "dh"
    REGIONAL_HOSPITAL = "rh"
    PSYCHIATRIC_HOSPITAL = "ph"
    TEACHING_HOSPITAL = "th"
    HOSPITAL = "hospital"
    HEALTH_CENTER = "hc"
    CHPS = "chps"
    POLYCLINIC = "pc"
    CLINIC = "c"
    ALL = {
        REGIONAL_MEDICAL_STORE: "regional medical store",
        REGIONAL_HOSPITAL: "regional hospital",
        DISTRICT_HOSPITAL: "dh", 
        PSYCHIATRIC_HOSPITAL: "ph", 
        TEACHING_HOSPITAL: "th", 
        HOSPITAL: "hospital",
        HEALTH_CENTER: "health center",
        CHPS: "chps",
        POLYCLINIC: "pc",
        CLINIC: "clinic",
    }
    
class SupplyPointPolicies(object):
    POLICY_1 = {
            "EMERGENCY_LEVEL": 0.5,
            "REORDER_LEVEL": 1.5,
            "MAXIMUM_LEVEL":  3,
    }
    POLICY_2 = {
            "EMERGENCY_LEVEL": 0.5,
            "REORDER_LEVEL": 1.5,
            "MAXIMUM_LEVEL":  6,
    }
    STOCK_POLICIES = {
          SupplyPointCodes.REGIONAL_HOSPITAL: POLICY_1, 
          SupplyPointCodes.HOSPITAL: POLICY_1, 
          SupplyPointCodes.HEALTH_CENTER: POLICY_1, 
          SupplyPointCodes.CHPS: POLICY_1, 
          SupplyPointCodes.POLYCLINIC: POLICY_1, 
          SupplyPointCodes.CLINIC: POLICY_1, 
          SupplyPointCodes.DISTRICT_HOSPITAL: POLICY_1, 
          SupplyPointCodes.PSYCHIATRIC_HOSPITAL: POLICY_1, 
          SupplyPointCodes.TEACHING_HOSPITAL: POLICY_1, 
          SupplyPointCodes.REGIONAL_MEDICAL_STORE: POLICY_2
    }

class LocationCodes(object):
    """
    These correspond to LocationType.code
    """
    COUNTRY = "country"
    REGION = "region"
    DISTRICT = "district"
    FACILITY = "facility"

def has_permissions_to(contact, operation):
    # one might want to use the responsibilities framework to manage
    # this but currently it seems strange that we'd have such tight
    # coupling between app logic and database logic, so it's here
    from logistics.models import ContactRole
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
    from logistics.models import SupplyPointType
    return SupplyPointType.objects.get(pk=HSA)

def hsa_location_type():
    """
    The location type for HSAs
    """
    from rapidsms.contrib.locations.models import LocationType
    return LocationType.objects.get(slug=HSA)
    
class Messages(object):
    SUPERVISOR_TITLE = 'DHIO'
    GET_HELP_MESSAGE = "Please contact your %(supervisor)s for assistance." % {'supervisor' : SUPERVISOR_TITLE}
    BAD_CODE_ERROR = ("%(code)s is not a recognized commodity code. "
                      "Please contact your DHIO for assistance.")
    NO_CODE_ERROR = "Stock report should contain at least one product code. " + \
                    "Please contact your %(supervisor)s for assistance." % {'supervisor' : SUPERVISOR_TITLE}
    NO_QUANTITY_ERROR ="Stock report should contain quantity of stock on hand. " + \
                                 "Please contact your %(supervisor)s for assistance." % {'supervisor': SUPERVISOR_TITLE}
    NO_SUPPLY_POINT_MESSAGE = "You are not associated with a facility. Please contact your DHIO for assistance."
    RECEIPT_CONFIRM = 'Thank you, you reported receipts for %(products)s.'
    REGISTER_MESSAGE = "You must be registered on EWS " + \
                       "before you can submit a stock report. " + \
                       "Please contact your %(supervisor)s." % {'supervisor' : SUPERVISOR_TITLE}
    REGISTRATION_REQUIRED_MESSAGE = REGISTER_MESSAGE
    SOH_HELP_MESSAGE = "To report stock on hand, send SOH [space] [product code] [space] [amount]"
    HELP_TEXT = "Txt 'help stock' 4 the format of stock reports; 'help codes' 4 commodity codes; 'start' or 'stop' 2 start and stop reminders; 'status' 2 check ur registration."
    
    REQ_SUBMITTED = "Thank you for confirming you have submitted your requisition this month."
    REQ_NOT_SUBMITTED = "Please submit your requisition form as soon as possible."

    # scheduled reminders
    STOCK_ON_HAND_REMINDER = 'Hi %(name)s! Please text your stock report tomorrow Friday by 2:00 pm. Your stock report can help save lives.'
    SECOND_STOCK_ON_HAND_REMINDER = 'Hi %(name)s, we did not receive your stock report last Friday. Please text your stock report as soon as possible.'
    SECOND_INCOMPLETE_SOH_REMINDER = 'Hi %(name)s, your facility is missing a few SMS stock reports. Please report on: %(products)s.'
    THIRD_STOCK_ON_HAND_REMINDER = 'Dear %(name)s, your facility has not reported its stock this week. Please make sure that the SMS stock report is submitted.'
    INCOMPLETE_SOH_TO_SUPER = 'Dear %(name)s, %(facility)s\'s SMS stock report was INCOMPLETE. Please report for: %(products)s'
    RRIRV_REMINDER = "Dear %(name)s, have you submitted your RRIRV forms this month? Please reply 'yes' or 'no'"

    # reports
    NUMBER_OF_SUPPLY_POINTS = "Number of Facilities"

class Alerts(object):
    pass
