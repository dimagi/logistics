from datetime import datetime
from djtables import Table, Column
from djtables.column import DateColumn
from logistics_project.apps.tanzania.models import SupplyPointStatusTypes, SupplyPointStatusValues,\
    DeliveryGroups
from logistics_project.apps.tanzania.utils import calc_lead_time
from utils import latest_status
from rapidsms.models import Contact
from django.template import defaultfilters
from django.utils.translation import ugettext as _

class MonthTable(Table):

    def __init__(self, *args, **kwargs):
        if 'month' in kwargs and 'year' in kwargs:
            self.month = kwargs['month']
            self.year = kwargs['year']
            del kwargs['month'], kwargs['year']
        else:
            self.month = datetime.utcnow().month
            self.year = datetime.utcnow().year

        super(MonthTable, self).__init__(**kwargs)

def _latest_status_or_none(cell, type, attr, value=None):
    t = latest_status(cell.object, type, month=cell.row.table.month, year=cell.row.table.year, value=value)
    if t and attr:
        return getattr(t, attr, None)
    return None

def _default_contact(supply_point):
    qs = Contact.objects.filter(supply_point=supply_point)
    if qs.exists():
        contact = qs[0]
        return "%s (%s) %s" % (contact, contact.role, 
                               contact.default_connection.identity if contact.default_connection else "")
    return None

def _dg(supply_point):
    return supply_point.groups.all()[0].code if supply_point.groups.exists() else None

def supply_point_link(cell):
    from logistics_project.apps.tanzania.views import tz_location_url
    return tz_location_url(cell.object.location)

class OrderingStatusTable(MonthTable):
    """
    Same as above but includes a column for the HSA
    """
    code = Column()
    delivery_group = Column(value=lambda cell: _dg(cell.object), sort_key_fn=_dg, name="Delivery Group")
    name = Column(link=supply_point_link)
    randr_status = Column(sortable=False, name="R&R Status", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.R_AND_R_FACILITY, "name"))
    randr_date = DateColumn(sortable=False, name="R&R Date", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.R_AND_R_FACILITY, "status_date"))
    delivery_status = Column(sortable=False, name="Delivery Status", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.DELIVERY_FACILITY, "name"))
    delivery_date = DateColumn(sortable=False, name="Delivery Date", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.DELIVERY_FACILITY, "status_date"))

    class Meta:
        per_page = 9999
        order_by = '-code'

class RandRSubmittedColumn(DateColumn):
    # copied and modified from djtables DateColumn
    
    def render(self, cell):
        val = self.value(cell)
        if val:
            return super(RandRSubmittedColumn, self).render(cell)
        else:
            return _("Not reported")
    
def _randr_value(cell):
    return _latest_status_or_none(cell, SupplyPointStatusTypes.R_AND_R_FACILITY, "status_date", value=SupplyPointStatusValues.SUBMITTED)

def _randr_css_class(cell):
    val = _randr_value(cell)
    if val is None:
        return "warning_icon iconified"
    else:
        return "good_icon iconified"

class RandRReportingHistoryTable(MonthTable):
    code = Column()
    name = Column(name="Facility Name", value=lambda cell:cell.object.name)
    delivery_group = Column(value=lambda cell: _dg(cell.object), sort_key_fn=_dg, name="Delivery Group")

    submitted = RandRSubmittedColumn(name="R&R Submitted This Quarter",
                                     value=_randr_value,
                                     format="d M Y P",
                                     css_class=_randr_css_class)
    contact = Column(name="Contact", value=lambda cell: _default_contact(cell.object), sort_key_fn=_default_contact)
    lead_time = Column(name="Lead Time", value=lambda cell: calc_lead_time(cell.object, month=cell.row.table.month, year=cell.row.table.year))
    @property
    def submitting_group(self):
        return DeliveryGroups(self.month).current_submitting_group()

    class Meta:
        per_page = 9999

class SupervisionTable(MonthTable):
    code = Column(value=lambda cell:cell.object.code, name="MSD Code", titleized=False)
    name = Column(name="Facility Name", value=lambda cell: cell.object.name)
    delivery_group = Column(value=lambda cell: _dg(cell.object), sort_key_fn=_dg, name="Delivery Group")
    supervision_this_quarter = Column(sortable=False, name="Supervision This Quarter", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.SUPERVISION_FACILITY, "name"))
    date = DateColumn(sortable=False, value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.SUPERVISION_FACILITY, "status_date"))

class StockOnHandTable(MonthTable):
    code = Column(value=lambda cell:cell.object.code, name="MSD Code")
    name = Column(name="Facility Name", value=lambda cell: cell.object.name)
    delivery_group = Column(value=lambda cell: _dg(cell.object), sort_key_fn=_dg, name="Delivery Group")
    last_reported = Column()

    class Meta:
        per_page = 9999

def _contact_or_none(cell, attr):
    try:
        return getattr(cell.object.user.contact, attr, "")
    except Contact.DoesNotExist:
        return ""

class NotesTable(Table):
    name = Column(sortable=False, value=lambda cell: cell.object.user.username)
    role = Column(sortable=False, value=lambda cell: _contact_or_none(cell, 'role'))
    date = DateColumn(format = "d M Y P")
    phone = Column(sortable=False, value=lambda cell: _contact_or_none(cell, 'phone'))
    text = Column()

    class Meta:
        per_page = 5
        order_by = "-date"