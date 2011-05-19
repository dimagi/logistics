#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf import settings
from djtables import Table, Column
from djtables.column import DateColumn
from logistics.apps.registration.tables import list_commodities,\
    contact_edit_link
from django.core.urlresolvers import reverse


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

    class Meta:
        order_by = 'supply_point__code'

class HSATable(Table):
    facility = Column(value=lambda cell: cell.object.supply_point.supplied_by,
                      sortable=False)
    name     = Column(link=lambda cell: reverse("malawi_hsa", args=[cell.object.pk]))
    id = Column(value=lambda cell: cell.object.hsa_id,
                sortable=False)
    commodities = Column(name="Responsible For These Commodities", 
                         value=list_commodities,
                         sortable=False)
    stocked_out = Column(name="Products stocked out",
                         value=lambda cell: cell.object.supply_point.stockout_count())
    emergency = Column(name="Products in emergency",
                         value=lambda cell: cell.object.supply_point.emergency_stock_count(),
                         sortable=False)
    ok = Column(name="Products in adequate supply",
                         value=lambda cell: cell.object.supply_point.adequate_stock_count(),
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

class StockRequestTable(Table):
    product = Column()
    status = Column()
    amount_requested = Column()
    amount_received = Column()
    
    requested_on = DateColumn()
    responded_on = DateColumn()
    received_on = DateColumn()

    is_emergency = Column()
    
    class Meta:
        order_by = '-requested_on'

