#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from djtables import Table, Column
from models import ILSGatewayColumn, ILSGatewayDateColumn, Product
from djtables.column import DateColumn
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

def _edit_link(cell):
    return reverse(
        "registration_edit",
        args=[cell.row.pk])

def _get_yes_no(cell):
    if  cell.object.primary:
        return _("Yes")
    else:
        return _("No")

class ContactDetailTable(Table):
    name = Column(link=_edit_link)
    language = Column()
    #role = Column()
    service_delivery_point = Column()
    primary = Column(value=_get_yes_no)

    class Meta:
        order_by = 'service_delivery_point__name'

def _get_role(cell):
    return _(cell.object.contact.contactdetail.role.name)

def _get_direction(cell):
    if  cell.object.direction == "I":
        return _("In")
    else:
        return _("Out")
    
class MessageHistoryTable(Table):
    contact = Column(value=lambda u: u.object.contact.name)
    direction = Column(value=_get_direction)
    role = Column(value=_get_role, sortable=False)
    phone = Column(value=lambda u: _(u.object.contact.contactdetail.phone()), sortable=False)
    date = DateColumn(format="H:m:s d/m/Y")
    text = Column()
    
def _get_stock_value(cell):
    return cell.object.stock_on_hand(cell.column.name)

def _get_mos_value(cell):
    return cell.object.months_of_stock(cell.column.name)
    
class CurrentStockStatusTable(Table):
    msd_code = ILSGatewayColumn(head_verbose="MSD Code")
    delivery_group = Column()
    name = Column(link=lambda cell: reverse("ilsgateway.views.facilities_detail", args=[cell.row.pk]))
    for product in Product.objects.all():
        exec("%s = ILSGatewayColumn(name='%s', value=_get_stock_value, head_verbose='%s', sortable=False)" % (product.sms_code, product.sms_code, product.name))

class CurrentMOSTable(Table):
    msd_code = ILSGatewayColumn(head_verbose="MSD Code")
    delivery_group = Column()
    name = Column(link=lambda cell: reverse("ilsgateway.views.facilities_detail", args=[cell.row.pk]))
    for product in Product.objects.all():
        exec("%s = ILSGatewayColumn(name='%s', value=_get_mos_value, head_verbose='%s', sortable=False, is_product=True)" % (product.sms_code, product.sms_code, product.name))

def _get_latest_randr_status(cell):
    if cell.object.randr_status():
        return cell.object.randr_status().status_type.name
    else:
        return ''

def _get_latest_randr_status_date(cell):
    if cell.object.randr_status():
        return cell.object.randr_status().status_date
    else:
        return ''

def _get_latest_delivery_status(cell):
    if cell.object.delivery_status():
        return cell.object.delivery_status().status_type.name
    else:
        return ''

def _get_latest_delivery_status_date(cell):
    if cell.object.delivery_status():
        return cell.object.delivery_status().status_date
    else:
        return ''


class OrderingTable(Table):
    msd_code = ILSGatewayColumn(head_verbose="MSD Code")
    delivery_group = Column()
    name = Column(link=lambda cell: reverse("ilsgateway.views.facilities_detail", args=[cell.row.pk]))
    randr_status = ILSGatewayColumn(head_verbose="R&R Status", value=_get_latest_randr_status, sortable=False)
    randr_status_date = ILSGatewayDateColumn(format="j N Y P", head_verbose="Date", value=_get_latest_randr_status_date, sortable=False)
    delivery_status = ILSGatewayColumn(head_verbose="Delivery Status", value=_get_latest_delivery_status, sortable=False)
    delivery_status_date = ILSGatewayDateColumn(format="j N Y P", head_verbose="Date", value=_get_latest_randr_status_date, sortable=False)    
