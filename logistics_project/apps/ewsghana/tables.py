#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.core.urlresolvers import reverse
from djtables import Table, Column
from djtables.column import DateColumn
from logistics.models import ProductStock
from logistics.tables import FacilityTable, _location

def _facility_view(cell):
    return reverse(
        'facility_detail',
        args=[cell.row.code])
def _facility_type(cell):
    return cell.object.type
def _consumption(cell):
    available = cell.object.consumptions_available()
    total = cell.object.commodities_stocked().count()
    return "%s of %s (%s)" % (available, 
                              total, 
                              'complete' if available == total 
                              else 'INCOMPLETE')
def _supervisor(cell):
    supervisors = cell.object.reportees()
    if supervisors:
        return supervisors[0].name
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
    supervisor = Column(value=_supervisor)
    consumption = Column(value=_consumption, 
                         name='Average Monthly Consumption', 
                         titleized=False)
    reporters = Column(value=_reporters, name='SMS Users')
    commodities_assigned = Column(value=_commodities_stocked, 
                                  titleized=False, 
                                  name='Registered to Report These Commodities via SMS')

    class Meta:
        order_by = 'location'
        per_page = 30

