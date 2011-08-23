from scheduler.decorators import businessday_before
from datetime import datetime, timedelta
from logistics.util import config
from logistics_project.apps.tanzania.reminders import send_reminders,\
    update_statuses
from logistics_project.apps.tanzania.models import DeliveryGroups,\
    SupplyPointStatusTypes, SupplyPointStatusValues
from rapidsms.models import Contact
from logistics_project.apps.tanzania.config import SupplyPointCodes
from dimagi.utils.dates import get_business_day_of_month_before

def get_facility_people(cutoff):
    # Facilities:
    # Group A gets a reminder every three months starting in January.
    # Then it rotates accordingly.
    current_group = DeliveryGroups().current_submitting_group()
    
    for contact in Contact.objects.filter\
            (supply_point__type__code=SupplyPointCodes.FACILITY,
             supply_point__groups__code__in=current_group):
        if not contact.supply_point.supplypointstatus_set.filter\
                (status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                 status_date__gte=cutoff).exists():
            yield contact
                
def get_district_people(cutoff):
    # All people at all Districts get all reminders each month.
    for contact in Contact.objects.filter\
            (supply_point__type__code=SupplyPointCodes.DISTRICT):
        if not contact.supply_point.supplypointstatus_set.filter\
                (status_type=SupplyPointStatusTypes.R_AND_R_DISTRICT,
                 status_date__gte=cutoff).exists():
            yield contact

def get_facility_cutoff():
    now = datetime.utcnow()
    return get_business_day_of_month_before(now.year, now.month, 5)

def get_district_cutoff():
    now = datetime.utcnow()
    return get_business_day_of_month_before(now.year, now.month, 13)

def _facility_shared():
    people = get_facility_people(get_facility_cutoff())
    send_reminders(people, 
                   config.Messages.REMINDER_R_AND_R_FACILITY)
    update_statuses(people, SupplyPointStatusTypes.R_AND_R_FACILITY,
                    SupplyPointStatusValues.REMINDER_SENT)
    
@businessday_before(5)
def first_facility():
    """Last business day before or on 5th day of the Submission month, 8:00am"""
    _facility_shared()
    
@businessday_before(10)
def second_facility():
    """Last business day before or on 10th day of the submission month, 8:00am"""
    _facility_shared()
    
@businessday_before(12)
def third_facility():
    """Last business day before or on 12th day of the submission month, 8:00am"""
    _facility_shared()

    
def _district_shared():
    people = get_district_people(get_district_cutoff())
    send_reminders(people, 
                   config.Messages.REMINDER_R_AND_R_DISTRICT)
    update_statuses(people, SupplyPointStatusTypes.R_AND_R_DISTRICT,
                    SupplyPointStatusValues.REMINDER_SENT)
    

@businessday_before(13)
def first_district():
    """Last business day before or on 13th day of the month, 8:00am"""
    _district_shared()
    
@businessday_before(15)
def second_district():
    """Last business day before or on 15th day of the month, 8:00am"""
    _district_shared()
    
@businessday_before(17)
def third_district():
    """Last business day before or on 17th day of the month, 2:00pm"""
    _district_shared()
    