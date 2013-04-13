from scheduler.decorators import businessday_before
from datetime import datetime
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
    # Group A gets a reminder every three months starting in March.
    # Then it rotates accordingly.
    # All people at all Districts get all reminders each month.
    # For facilities the reminder should go out if we haven't received 
    # any status of type of del_fac
    current_group = DeliveryGroups().current_delivering_group()
    
    for contact in Contact.objects.filter\
            (supply_point__type__code=SupplyPointCodes.FACILITY,
             supply_point__groups__code__in=current_group, is_active=True):
        if not contact.supply_point.supplypointstatus_set.filter\
                (status_type=SupplyPointStatusTypes.DELIVERY_FACILITY,
                 status_date__gte=cutoff).exists():
            yield contact
                
def get_district_people(cutoff):
    # All people at all Districts get all reminders each month.
    for contact in Contact.objects.filter\
            (supply_point__type__code=SupplyPointCodes.DISTRICT,
             is_active=True):
        if not contact.supply_point.supplypointstatus_set.filter\
                (status_type=SupplyPointStatusTypes.DELIVERY_DISTRICT,
                 status_date__gte=cutoff).exists():
            yield contact

def get_facility_cutoff():
    now = datetime.utcnow()
    return get_business_day_of_month_before(now.year, now.month, 15)

def get_district_cutoff():
    now = datetime.utcnow()
    return get_business_day_of_month_before(now.year, now.month, 13)

def _facility_shared():
    people = list(get_facility_people(get_facility_cutoff()))
    update_statuses(people, SupplyPointStatusTypes.DELIVERY_FACILITY,
                    SupplyPointStatusValues.REMINDER_SENT)
    send_reminders(people, config.Messages.REMINDER_DELIVERY_FACILITY)
    
@businessday_before(15)
def first_facility():
    """2:00pm"""
    _facility_shared()
    
@businessday_before(22)
def second_facility():
    """2:00pm"""
    _facility_shared()
    
@businessday_before(30)
def third_facility():
    """2:00pm"""
    _facility_shared()
    
def _district_shared():
    people = list(get_district_people(get_district_cutoff()))
    send_reminders(people, 
                   config.Messages.REMINDER_DELIVERY_DISTRICT)
    update_statuses(people, SupplyPointStatusTypes.DELIVERY_DISTRICT,
                    SupplyPointStatusValues.REMINDER_SENT)
    

@businessday_before(13)
def first_district():
    """2:00pm"""
    _district_shared()
    
@businessday_before(20)
def second_district():
    """2:00pm"""
    _district_shared()
    
@businessday_before(28)
def third_district():
    """2:00pm"""
    _district_shared()