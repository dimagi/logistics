from django.conf import settings
from django.core.urlresolvers import reverse
from djtables import Table, Column
from logistics_project.apps.malawi.util import get_managed_products_for_contact


def contact_edit_link(cell):
    registration_edit_view = 'registration_edit'
    if hasattr(settings,'SMS_REGISTRATION_EDIT'):
        registration_edit_view = settings.SMS_REGISTRATION_EDIT
    return reverse(
        registration_edit_view,
        args=[cell.row.pk])

def render_supply_point(cell):
    if cell.object.supply_point:
        return cell.object.supply_point.name

def list_commodities(cell):
    commodities = get_managed_products_for_contact(cell.object)
    if commodities.count() == 0:
        return "None"
    return " ".join(commodities.order_by('name').values_list('sms_code', flat=True))

class ContactTable(Table):
    name     = Column(link=contact_edit_link)
    supply_point = Column(value=render_supply_point, name="Supply Point",
                          sortable=False)
    phone = Column(value=lambda cell: cell.object.phone, sortable=False)

    class Meta:
        order_by = 'supply_point'
        per_page = 30
