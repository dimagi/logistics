#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.core.urlresolvers import reverse
from djtables import Table, Column
from djtables.column import DateColumn
from logistics.apps.logistics.models import ProductStock
from logistics.apps.logistics.tables import FacilityTable, _location

def _facility_view(cell):
    return reverse(
        'facility_detail',
        args=[cell.row.code])
def _facility_type(cell):
    return cell.object.type
def _consumption(cell):
    are_consumptions_set = cell.object.are_consumptions_set()
    if are_consumptions_set:
        return "INCOMPLETE"
    return "Complete"
def _supervisor(cell):
    supervisors = cell.object.reportees()#Contact.objects.filter(supply_point=cell.object).filter(role__responsibilities__code=config.Responsibilities.REPORTEE_RESPONSIBILITY)
    if supervisors:
        return supervisors[0].name
    return "None"
def _reporters(cell):
    reporters = cell.object.reporters()#Contact.objects.filter(supply_point=cell.object).filter(role__responsibilities__code=config.Responsibilities.STOCK_ON_HAND_RESPONSIBILITY)
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
    consumption = Column(value=_consumption)
    reporters = Column(value=_reporters)
    commodities_assigned = Column(value=_commodities_stocked)

    class Meta:
        order_by = 'location'
        per_page = 30

