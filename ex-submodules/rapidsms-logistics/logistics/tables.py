#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from __future__ import unicode_literals
from builtins import object
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.urls import reverse
from djtables import Table, Column
from djtables.column import DateColumn


class MonthTable(Table):

    def __init__(self, *args, **kwargs):
        if 'month' in kwargs and 'year' in kwargs:
            self.month = kwargs['month']
            self.year = kwargs['year']
            self.day = kwargs['day']
            del kwargs['month'], kwargs['year'], kwargs['day']

        else:
            self.month = datetime.utcnow().month
            self.year = datetime.utcnow().year
            self.day = datetime.utcnow().day

        super(MonthTable, self).__init__(**kwargs)


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

    class Meta(object):
        order_by = 'name'

class ShortMessageTable(Table):

    date = DateColumn(format="H:i d/m/Y", sortable=False)
    direction = Column(sortable=False)
    text = Column(css_class="message", sortable=False)

class FullMessageTable(Table):
    contact = Column(value=lambda cell:cell.object.contact.name)
    direction = Column(sortable=False)
    role = Column(value=lambda cell:cell.object.contact.role.name)
    number = Column(value=lambda cell:cell.object.contact.phone)
    date = DateColumn(format="H:i d/m/Y", sortable=False)
    text = Column(css_class="message", sortable=False)

class ReportingTable(Table):
    name = Column(sortable=False)
    last_reported = DateColumn(name="Last Reported on",
                               value=lambda cell: cell.object.last_reported \
                                    if cell.object.last_reported else "never",
                               format="M d, h:i A", 
                               sortable=False,
                               sort_key_fn=lambda obj: obj.last_reported,
                               css_class="tabledate")
    
    class Meta(object):
        order_by = '-last_reported'

def _parent_or_nothing(location):
    if location is None or \
       location.tree_parent is None:
        return None
    return location.tree_parent
def _facility(cell):
    if cell.object.contact is None or \
     cell.object.contact.supply_point is None:
        return None
    return cell.object.contact.supply_point
def _district(cell):
    fac = _facility(cell)
    if fac:
        dist = _parent_or_nothing(fac.location)
        return dist
def _district_name(cell):
    d = _district(cell)
    return d.name if d else ""
def _region(cell):
    r = _parent_or_nothing(_district(cell))
    return r.name if r else ""
def _connection(cell):
    return cell.object.connection.identity
class MessageTable(Table):
    # this is temporary, until i fix ModelTable!
    contact = Column()
    mobile_number = Column(value=_connection, sortable=False)
    direction = Column()
    date = DateColumn(format="H:i d/m")
    text = Column(css_class="message")
    facility = Column(value=_facility, sortable=False)
    district = Column(value=_district, sortable=False)
    region = Column(value=_region, sortable=False)

    class Meta(object):
        order_by = '-date'
