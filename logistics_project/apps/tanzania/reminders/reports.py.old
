"""
Reports that go out
"""
from scheduler.decorators import businessday_before, businessday
from rapidsms.models import Contact
from logistics_project.apps.tanzania.config import SupplyPointCodes
from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown
from datetime import datetime
from rapidsms.contrib.messaging.utils import send_message
from logistics.util import config

def get_district_people():
    for contact in Contact.objects.filter\
            (supply_point__type__code=SupplyPointCodes.DISTRICT):
        yield contact
        
def construct_randr_summary(supply_point, year, month):
    children = supply_point.children()
    breakdown = SupplyPointStatusBreakdown(children, datetime(year, month, 1))
    return {"submitted": breakdown.submitted.count(),
            "not_submitted": breakdown.not_submitted.count(),
            "not_responding": breakdown.not_responding.count(),
            "total": children.count()}
    
@businessday(-1)
def delivery_summary():
    """
    "Deliveries - 5/10 received, 4/10 did not receive, 1/10 users did not reply" - last business day of month 3pm
    """
    pass

@businessday(6)
def soh_summary():    
    """
    "SOH - 6/10 reported, 4/10 did not reply - 6th of the month @ 3pm
    """

@businessday_before(17)
def randr_summary():
    """
    "R&R - 6/10 submitted, 2/10 did not submit, 3/10 did not reply" - 17th of the month @ 3pm
    """
    for contact in get_district_people():
        send_message(contact.connection,
                     _(config.Messages.REMINDER_MONTHLY_RANDR_SUMMARY, 
                       **construct_randr_summary(contact.supply_point)))