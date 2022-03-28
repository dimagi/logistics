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


def _edit_org_link(cell):
    return reverse("malawi_edit_organization", args=[cell.row.pk])
    

class OrganizationTable(Table):
    name     = Column(link=_edit_org_link)
    members  = Column(value=lambda cell: Contact.objects.filter(organization=cell.object).count(),
                      sortable=False)
    
    class Meta:
        order_by = 'name'


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
