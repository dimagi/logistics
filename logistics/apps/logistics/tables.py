#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import settings
from django.core.urlresolvers import reverse
from djtables import Table, Column
from djtables.column import DateColumn

def _edit_facility_link(cell):
    return reverse(
        'facility_edit',
        args=[cell.row.pk])
def _location(cell):
    return cell.object.location
class FacilityTable(Table):
    name = Column(link=_edit_facility_link)
    location = Column(value=_location)

    class Meta:
        order_by = 'location'
        per_page = 30


def _edit_commodity_link(cell):
    return reverse(
        'commodity_edit',
        args=[cell.row.pk])
def _code(cell):
    return cell.object.sms_code
def _type(cell):
    return cell.object.type
class CommodityTable(Table):
    name = Column(link=_edit_commodity_link)
    sms_code = Column(value=_code)
    type = Column(value=_type)

    class Meta:
        order_by = 'name'

class ShortMessageTable(Table):

    date = DateColumn(format="H:i d/m/Y", sortable=False)
    direction = Column(sortable=False)
    text = Column(css_class="message", sortable=False)

    
class ReportingTable(Table):
    name = Column(sortable=False)
    last_reported = DateColumn(name="Last Reported on",
                               value=lambda cell: cell.object.last_reported \
                                    if cell.object.last_reported else "never",
                               format="M d, h:m A", 
                               sortable=False,
                               css_class="tabledate")
    
    class Meta:
        order_by = '-last_reported'

def _facility(cell):
    if cell.object.contact is None or \
     cell.object.contact.supply_point is None:
        return None
    return cell.object.contact.supply_point
def _district(cell):
    facility = _facility(cell)
    if facility is None or \
      facility.location is None or \
      facility.location.tree_parent is None:
        return None
    return facility.location.tree_parent.name
def _connection(cell):
    return cell.object.connection.identity
class MessageTable(Table):
    # this is temporary, until i fix ModelTable!
    contact = Column()
    mobile_number = Column(value=_connection)
    direction = Column()
    date = DateColumn(format="H:i d/m")
    text = Column(css_class="message")
    facility = Column(value=_facility)
    location = Column(value=_district)

    class Meta:
        order_by = '-date'
