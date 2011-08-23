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
from logistics_project.apps.tanzania.utils import sps_with_latest_status,\
    supply_points_with_latest_status_by_datespan
from logistics_project.apps.tanzania.models import SupplyPointStatusTypes,\
    SupplyPointStatusValues
from logistics_project.apps.tanzania.reminders import stockonhand, randr, delivery
from dimagi.utils.dates import DateSpan

def get_district_people():
    for contact in Contact.objects.filter\
            (supply_point__type__code=SupplyPointCodes.DISTRICT):
        yield contact
        
def _construct_status_dict(status_type, status_values, supply_points, datespan):
    ret = {}
    for status in status_values:
        ret[status] = supply_points_with_latest_status_by_datespan\
                        (sps=supply_points, 
                         status_type=status_type,
                         status_value=status,
                         datespan=datespan).count()
    ret["total"] = supply_points.count()
    ret["not_responding"] = supply_points.count() - \
                                sum(v for k, v in ret.items() if k != "total")
    return ret

def construct_randr_summary(supply_point):
    children = supply_point.children()
    # assumes being run in the same month we care about.
    cutoff = randr.get_facility_cutoff()
    return _construct_status_dict(SupplyPointStatusTypes.R_AND_R_FACILITY,
                                  [SupplyPointStatusValues.SUBMITTED, 
                                   SupplyPointStatusValues.NOT_SUBMITTED],
                                  children, DateSpan(cutoff, datetime.utcnow()))
    
def construct_soh_summary(supply_point):
    children = supply_point.children()
    # assumes being run in month after the cutoff date (last day of previous month)
    cutoff = stockonhand.get_cutoff(*stockonhand.last_yearmonth())
    return _construct_status_dict(SupplyPointStatusTypes.SOH_FACILITY, 
                                  [SupplyPointStatusValues.SUBMITTED],
                                  children, DateSpan(cutoff, datetime.utcnow()))
    
def construct_delivery_summary(supply_point):
    children = supply_point.children()
    # assumes being run in the same month we care about.
    cutoff = delivery.get_facility_cutoff()
    return _construct_status_dict(SupplyPointStatusTypes.DELIVERY_FACILITY,
                                  [SupplyPointStatusValues.SUBMITTED, 
                                   SupplyPointStatusValues.NOT_SUBMITTED],
                                  children, DateSpan(cutoff, datetime.utcnow()))
    
@businessday(-1)
def delivery_summary():
    """
    "Deliveries - 5/10 received, 4/10 did not receive, 1/10 users did not reply" - last business day of month 3pm
    """
    for contact in get_district_people():
        send_message(contact.connection,
                     _(config.Messages.REMINDER_MONTHLY_DELIVERY_SUMMARY, 
                       **construct_delivery_summary(contact.supply_point)))
        


@businessday(6)
def soh_summary():    
    """
    "SOH - 6/10 reported, 4/10 did not reply" - 6th of the month @ 3pm
    """
    for contact in get_district_people():
        send_message(contact.connection,
                     _(config.Messages.REMINDER_MONTHLY_SOH_SUMMARY, 
                       **construct_soh_summary(contact.supply_point)))
        
@businessday_before(17)
def randr_summary():
    """
    "R&R - 6/10 submitted, 2/10 did not submit, 3/10 did not reply" - 17th of the month @ 3pm
    """
    for contact in get_district_people():
        send_message(contact.connection,
                     _(config.Messages.REMINDER_MONTHLY_RANDR_SUMMARY, 
                       **construct_randr_summary(contact.supply_point)))