#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf import settings
from djtables import Table, Column
from djtables.column import DateColumn
from logistics_project.apps.registration.tables import list_commodities,\
    contact_edit_link
from django.core.urlresolvers import reverse
from django.template.defaultfilters import yesno
from logistics.models import StockRequestStatus
from rapidsms.models import Contact


class MalawiContactTable(Table):
    name     = Column(link=contact_edit_link)
    role = Column()
    hsa_id = Column(value=lambda cell: cell.object.hsa_id,
                    name="HSA Id",
                    sortable=False)
    supply_point = Column(value=lambda cell: cell.object.associated_supply_point_name,
                          name="Supply Point",
                          sortable=False)
    phone = Column(value=lambda cell: cell.object.phone, 
                   name="Phone Number",
                   sortable=False)
    commodities = Column(name="Responsible For These Commodities", 
                         value=list_commodities,
                         sortable=False)
    organization = Column()
    
    class Meta:
        order_by = 'supply_point__code'

def _edit_org_link(cell):
    return reverse("malawi_edit_organization", args=[cell.row.pk])
    
class OrganizationTable(Table):
    name     = Column(link=_edit_org_link)
    members  = Column(value=lambda cell: Contact.objects.filter(organization=cell.object).count(),
                      sortable=False)
    
    class Meta:
        order_by = 'name'


class HSATable(Table):
    facility = Column(value=lambda cell: cell.object.supply_point.supplied_by,
                      sortable=False)
    name     = Column(link=lambda cell: reverse("malawi_hsa", args=[cell.object.supply_point.code]))
    id = Column(value=lambda cell: cell.object.hsa_id,
                sortable=False)
    commodities = Column(name="Responsible For These Commodities", 
                         value=list_commodities,
                         sortable=False)
    stocked_out = Column(name="Products stocked out",
                         value=lambda cell: cell.object.supply_point.stockout_count(),
                         sortable=False)
    emergency = Column(name="Products in emergency",
                         value=lambda cell: cell.object.supply_point.emergency_stock_count(),
                         sortable=False)
    ok = Column(name="Products in adequate supply",
                         value=lambda cell: cell.object.supply_point.adequate_supply_count(),
                         sortable=False)
    overstocked = Column(name="Products overstocked",
                         value=lambda cell: cell.object.supply_point.overstocked_count(),
                         sortable=False)
    last_seen = Column(name="Last message",
                       value=lambda cell: cell.object.last_message.date.strftime("%b-%d-%Y") if cell.object.last_message else "n/a",
                       sortable=False)
    
    class Meta:
        order_by = 'supply_point__code'

class MalawiLocationTable(Table):
    name     = Column()
    type = Column()
    code = Column()
    
    class Meta:
        order_by = 'type'

class MalawiProductTable(Table):
    name = Column()
    sms_code = Column()
    average_monthly_consumption = Column()
    emergency_order_level = Column()
    type = Column()
    
    class Meta:
        order_by = 'name'

class EmergencyColumn(Column):
    def __init__(self):
        super(EmergencyColumn, self).__init__(name="Is Emergency?",
                                              sortable=False,
                                              value=lambda cell: yesno(cell.object.is_emergency))
        
def status_display(status):
    if status == StockRequestStatus.APPROVED:
        return "order ready"
    else: 
        return status.replace("_", " ")

class StatusColumn(Column):
    def __init__(self):
        super(StatusColumn, self).__init__(name="Status",
                                           sortable=False,
                                           value=lambda cell: status_display(cell.object.status))
        
class StockRequestTable(Table):
    product = Column()
    is_emergency = EmergencyColumn()
    balance = Column()
    amount_requested = Column()
    amount_received = Column()
    requested_on = DateColumn()
    responded_on = DateColumn()
    received_on = DateColumn()
    status = StatusColumn()
    
    class Meta:
        order_by = '-requested_on'

