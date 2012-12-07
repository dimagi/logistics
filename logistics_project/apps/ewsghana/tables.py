#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from itertools import chain
from django.core.urlresolvers import reverse
from djtables import Table, Column
from djtables.column import DateColumn
from logistics.models import ProductStock
from logistics.tables import FacilityTable, _location
from rapidsms.contrib.messagelog.tables import MessageTable

def _facility_view(cell):
    return reverse(
        'facility_detail',
        args=[cell.row.code])
def _facility_type(cell):
    return cell.object.type
def _consumption(cell):
    available = cell.object.stocked_consumptions_available()
    total = cell.object.commodities_stocked().count()
    return "%s of %s (%s)" % (available,
                              total, 
                              'complete' if available >= total 
                              else 'INCOMPLETE')
def _supervisor(cell):
    supervisors = list(chain(cell.object.reportees(), 
                             cell.object.supervised_by.reportees() if cell.object.supervised_by else []))
    if supervisors:
        return ", ".join([s.name for s in supervisors])
    return "None"
def _reporters(cell):
    reporters = cell.object.reporters()
    if reporters:
        return ", ".join([r.name for r in reporters])
    return "None"
def _commodities_stocked(cell):
    commodities = cell.object.commodities_stocked()
    if commodities:
        return " ".join([c.code for c in set(commodities)])
    return None
class FacilityDetailTable(FacilityTable):
    name = Column(link=_facility_view)
    type = Column(value=_facility_type)
    supervisor = Column(value=_supervisor, sortable=False)
    consumption = Column(value=_consumption, 
                         name='Average Monthly Consumption', 
                         titleized=False, 
                         sortable=False)
    reporters = Column(value=_reporters, name='SMS Users', sortable=False)
    commodities_assigned = Column(value=_commodities_stocked, 
                                  titleized=False, sortable=False, 
                                  name='Registered to Report These Commodities via SMS')

    class Meta:
        order_by = 'location'
        per_page = 30

class AuditLogTable(Table):
    date = DateColumn(format="H:i d/m/Y")
    user = Column()
    access_type = Column()
    designation = Column()
    organization = Column()
    facility = Column()
    location = Column()
    first_name = Column()
    last_name = Column()

    class Meta:
        order_by = '-date'

def _supply_point(cell):
    if cell.object.contact and cell.object.contact.supply_point:
        return cell.object.contact.supply_point
    return None
def _connection(cell):
    if cell.object.connection:
        return cell.object.connection.identity
    return None
class EWSMessageTable(MessageTable):
    contact = Column()
    connection = Column(value=_connection)
    direction = Column()
    date = DateColumn(format="H:i d/m/y")
    text = Column(css_class="message")
    supply_point = Column(value=_supply_point)

    class Meta:
        order_by = '-date'
