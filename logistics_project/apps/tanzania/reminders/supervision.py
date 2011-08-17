from scheduler.decorators import businessday
from logistics.util import config
from logistics_project.apps.tanzania.reminders import send_reminders

def get_people():
    # TODO, update this appropriately
    return []

@businessday(-1)
def first():
    """Last business day of the month-2:15 PM"""
    send_reminders(get_people(), config.Messages.REMINDER_SUPERVISION)
    