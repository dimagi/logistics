from scheduler.decorators import businessday
from logistics.util import config
from logistics_project.apps.tanzania.config import SupplyPointCodes
from logistics_project.apps.tanzania.models import SupplyPointStatusTypes, SupplyPointStatusValues
from logistics_project.apps.tanzania.reminders import send_reminders, update_statuses
from logistics_project.apps.tanzania.reminders.randr import get_facility_cutoff
from rapidsms.models import Contact

def get_people():
    for contact in Contact.objects.filter(supply_point__type__code=SupplyPointCodes.FACILITY):
        print contact.supply_point.supplypointstatus_set.all()
        if not contact.supply_point.supplypointstatus_set.filter\
                (status_type=SupplyPointStatusTypes.SUPERVISION_FACILITY,
                 status_date__gte=get_facility_cutoff()).exists():
            yield contact

def set_supervision_statuses():
    update_statuses(get_people(), SupplyPointStatusTypes.SUPERVISION_FACILITY, SupplyPointStatusValues.REMINDER_SENT)

@businessday(1)
def first():
    """Last business day of the month-2:15 PM"""
    set_supervision_statuses()