from scheduler.decorators import businessday_before
from datetime import datetime, timedelta
from logistics.util import config
from logistics_project.apps.tanzania.reminders import send_reminders
from logistics_project.apps.tanzania.models import DeliveryGroups,\
    SupplyPointStatusTypes
from rapidsms.models import Contact
from logistics_project.apps.tanzania.config import SupplyPointCodes

def get_facility_people():
    # Facilities:
    # Group A gets a reminder every three months starting in March.
    # Then it rotates accordingly.
    # All people at all Districts get all reminders each month.
    # For facilities the reminder should go out if we haven't received 
    # any status of type of del_fac
    current_group = DeliveryGroups().current_delivering_group()
    
    # TODO, change totally arbitrary cutoff
    cutoff = datetime.utcnow() - timedelta(days=10)
    for contact in Contact.objects.filter\
            (supply_point__type__code=SupplyPointCodes.FACILITY,
             supply_point__groups__code__in=current_group):
        if not contact.supply_point.supplypointstatus_set.filter\
                (status_type=SupplyPointStatusTypes.DELIVERY_FACILITY,
                 status_date__gte=cutoff).exists():
            yield contact
                
def get_district_people():
    # All people at all Districts get all reminders each month.
    # TODO, change totally arbitrary cutoff
    cutoff = datetime.utcnow() - timedelta(days=10)
    for contact in Contact.objects.filter\
            (supply_point__type__code=SupplyPointCodes.DISTRICT):
        if not contact.supply_point.supplypointstatus_set.filter\
                (status_type=SupplyPointStatusTypes.DELIVERY_DISTRICT,
                 status_date__gte=cutoff).exists():
            yield contact


@businessday_before(15)
def first_facility():
    """2:00pm"""
    send_reminders(get_facility_people(), config.Messages.REMINDER_DELIVERY_FACILITY)
    
@businessday_before(22)
def second_facility():
    """2:00pm"""
    send_reminders(get_facility_people(), config.Messages.REMINDER_DELIVERY_FACILITY)
    
@businessday_before(30)
def third_facility():
    """2:00pm"""
    send_reminders(get_facility_people(), config.Messages.REMINDER_DELIVERY_FACILITY)
    
@businessday_before(13)
def first_district():
    """2:00pm"""
    send_reminders(get_district_people(), config.Messages.REMINDER_DELIVERY_DISTRICT)
    
@businessday_before(20)
def second_district():
    """2:00pm"""
    send_reminders(get_district_people(), config.Messages.REMINDER_DELIVERY_DISTRICT)
    
@businessday_before(28)
def third_district():
    """2:00pm"""
    send_reminders(get_district_people(), config.Messages.REMINDER_DELIVERY_DISTRICT)
