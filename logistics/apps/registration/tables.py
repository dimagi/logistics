#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import settings
from django.core.urlresolvers import reverse
from djtables import Table, Column
from rapidsms.models import Contact


def _edit_link(cell):
    return reverse(
        settings.REGISTRATION_EDIT,
        args=[cell.row.pk])

def _any_identity(cell):
    if cell.object.connection_set.count() > 0:
        return cell.object.connection_set.all()[0].identity

def _list_commodities(cell):
    commodities = cell.object.commodities.all()
    if commodities.count() == 0:
        return "None"
    return " ".join(commodities.order_by('name').values_list('sms_code', flat=True))

class ContactTable(Table):
    name     = Column(link=_edit_link)
    identity = Column(value=_any_identity)
    commodities = Column(name="Responsible For These Commodities", 
                         value=_list_commodities)

    class Meta:
        order_by = 'name'
