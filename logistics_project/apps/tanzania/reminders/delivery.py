from scheduler.decorators import businessday, businessday_before
from logistics.util import config
from logistics_project.apps.tanzania.reminders import send_reminders

def get_people():
    # TODO, update this appropriately
    return []

@businessday_before(15)
def first_facility():
    """2:00pm"""
    send_reminders(get_people(), config.Messages.REMINDER_DELIVERY_FACILITY)
    
@businessday_before(22)
def second_facility():
    """2:00pm"""
    send_reminders(get_people(), config.Messages.REMINDER_DELIVERY_FACILITY)
    
@businessday_before(30)
def third_facility():
    """2:00pm"""
    send_reminders(get_people(), config.Messages.REMINDER_DELIVERY_FACILITY)
    
@businessday_before(13)
def first_district():
    """2:00pm"""
    send_reminders(get_people(), config.Messages.REMINDER_DELIVERY_DISTRICT)
    
@businessday_before(20)
def second_district():
    """2:00pm"""
    send_reminders(get_people(), config.Messages.REMINDER_DELIVERY_DISTRICT)
    
@businessday_before(28)
def third_district():
    """2:00pm"""
    send_reminders(get_people(), config.Messages.REMINDER_DELIVERY_DISTRICT)
