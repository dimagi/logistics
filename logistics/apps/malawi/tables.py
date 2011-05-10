#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf import settings
from djtables import Table, Column
from djtables.column import DateColumn
from logistics.apps.registration.tables import list_commodities,\
    contact_edit_link


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

class MalawiLocationTable(Table):
    name     = Column()
    type = Column()
    code = Column()
    
    class Meta:
        order_by = 'type'
