from scheduler.decorators import businessday_before
from datetime import datetime, timedelta
from logistics.util import config
from logistics_project.apps.tanzania.reminders import send_reminders
from logistics_project.apps.tanzania.models import DeliveryGroups,\
    SupplyPointStatusTypes
from rapidsms.models import Contact
from logistics_project.apps.tanzania.config import SupplyPointCodes

def get_facility_people():
    # TODO, update this appropriately
    # Facilities:
    # Group A gets a reminder every three months starting in January.
    # Then it rotates accordingly.
    current_group = DeliveryGroups.current_submitting_group()
    
    # TODO, change totally arbitrary cutoff
    cutoff = datetime.utcnow() - timedelta(days=10)
    for contact in Contact.objects.filter\
            (supply_point__type__code=SupplyPointCodes.FACILITY,
             supply_point__groups__code__in=current_group):
        if not contact.supply_point.supplypointstatus_set.filter\
                (status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                 status_date__gte=cutoff).exists():
            yield contact
                
def get_district_people():
    # All people at all Districts get all reminders each month.
    # TODO, change totally arbitrary cutoff
    cutoff = datetime.utcnow() - timedelta(days=10)
    for contact in Contact.objects.filter\
            (supply_point__type__code=SupplyPointCodes.DISTRICT):
        if not contact.supply_point.supplypointstatus_set.filter\
                (status_type=SupplyPointStatusTypes.R_AND_R_DISTRICT,
                 status_date__gte=cutoff).exists():
            yield contact

@businessday_before(5)
def first_facility():
    """Last business day before or on 5th day of the Submission month, 8:00am"""
    send_reminders(get_facility_people(), config.Messages.REMINDER_R_AND_R_FACILITY)
    
@businessday_before(10)
def second_facility():
    """Last business day before or on 10th day of the submission month, 8:00am"""
    send_reminders(get_facility_people(), config.Messages.REMINDER_R_AND_R_FACILITY)
    
@businessday_before(12)
def third_facility():
    """Last business day before or on 12th day of the submission month, 8:00am"""
    send_reminders(get_facility_people(), config.Messages.REMINDER_R_AND_R_FACILITY)
    
@businessday_before(13)
def first_district():
    """Last business day before or on 13th day of the month, 8:00am"""
    send_reminders(get_district_people(), config.Messages.REMINDER_R_AND_R_DISTRICT)
    
@businessday_before(15)
def second_district():
    """Last business day before or on 15th day of the month, 8:00am"""
    send_reminders(get_district_people(), config.Messages.REMINDER_R_AND_R_DISTRICT)
    
@businessday_before(17)
def third_district():
    """Last business day before or on 17th day of the month, 2:00pm"""
    send_reminders(get_district_people(), config.Messages.REMINDER_R_AND_R_DISTRICT)
    