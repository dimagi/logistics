from scheduler.decorators import businessday, businessday_before
from logistics.util import config
from logistics_project.apps.tanzania.reminders import send_reminders

def get_people():
    # TODO, update this appropriately
    return []

@businessday_before(5)
def first_facility():
    """Last business day before or on 5th day of the Submission month, 8:00am"""
    send_reminders(get_people(), config.Messages.REMINDER_R_AND_R_FACILITY)
    
@businessday_before(10)
def second_facility():
    """Last business day before or on 10th day of the submission month, 8:00am"""
    send_reminders(get_people(), config.Messages.REMINDER_R_AND_R_FACILITY)
    
@businessday_before(12)
def third_facility():
    """Last business day before or on 12th day of the submission month, 8:00am"""
    send_reminders(get_people(), config.Messages.REMINDER_R_AND_R_FACILITY)
    
@businessday_before(13)
def first_district():
    """Last business day before or on 13th day of the month, 8:00am"""
    send_reminders(get_people(), config.Messages.REMINDER_R_AND_R_DISTRICT)
    
@businessday_before(15)
def second_district():
    """Last business day before or on 15th day of the month, 8:00am"""
    send_reminders(get_people(), config.Messages.REMINDER_R_AND_R_DISTRICT)
    
@businessday_before(17)
def third_district():
    """Last business day before or on 17th day of the month, 2:00pm"""
    send_reminders(get_people(), config.Messages.REMINDER_R_AND_R_DISTRICT)
    