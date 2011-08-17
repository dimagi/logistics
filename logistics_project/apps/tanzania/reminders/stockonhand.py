from scheduler.decorators import businessday
from logistics.util import config
from logistics_project.apps.tanzania.reminders import send_reminders

def get_people():
    # TODO, update this appropriately
    return []

@businessday(-1)
def first():
    """Last business day of the month-2:00 PM"""
    send_reminders(get_people(), config.Messages.REMINDER_STOCKONHAND)
    
@businessday(1)
def second():
    """1st business day of the next month – 9:00am"""
    send_reminders(get_people(), config.Messages.REMINDER_STOCKONHAND)
    
@businessday(5)
def third():
    """5th  business day of the next month – 8:15am"""
    send_reminders(get_people(), config.Messages.REMINDER_STOCKONHAND)
    

    
    