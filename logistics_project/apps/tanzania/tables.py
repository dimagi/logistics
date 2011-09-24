from datetime import datetime
from django.template.defaultfilters import floatformat
from djtables import Table, Column
from djtables.column import DateColumn
from logistics_project.apps.tanzania.models import SupplyPointStatusTypes, SupplyPointStatusValues,\
    DeliveryGroups, OnTimeStates
from logistics_project.apps.tanzania.templatetags.tz_tags import last_report_span, last_report_cell
from logistics_project.apps.tanzania.utils import calc_lead_time, historical_response_rate, soh_reported_on_time
from logistics.models import SupplyPoint
from utils import latest_status
from rapidsms.models import Contact
from django.template import defaultfilters
from django.utils.translation import ugettext as _
from logistics.templatetags.logistics_report_tags import historical_stock, historical_months_of_stock


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
    group = supply_point.default_group 
    return group.code if group else "?"

def supply_point_link(cell):
    from logistics_project.apps.tanzania.views import tz_location_url
    return tz_location_url(cell.object.location)

class OrderingStatusTable(MonthTable):
    """
    Same as above but includes a column for the HSA
    """
    code = Column()
    name = Column(name="Facility Name", value=lambda cell: cell.object.name, sort_key_fn=lambda obj: obj.name, link=supply_point_link)
    delivery_group = Column(value=lambda cell: _dg(cell.object), sort_key_fn=_dg, name="D G")
    randr_status = Column(sortable=False, name="R&R Status", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.R_AND_R_FACILITY, "name"))
    randr_date = DateColumn(sortable=False, name="R&R Date", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.R_AND_R_FACILITY, "status_date"))
    delivery_status = Column(sortable=False, name="Delivery Status", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.DELIVERY_FACILITY, "name"))
    delivery_date = DateColumn(sortable=False, name="Delivery Date", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.DELIVERY_FACILITY, "status_date"))

    class Meta:
        per_page = 9999
        order_by = ["D G", "Facility Name"]

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

def _hrr_randr(sp):
    r = historical_response_rate(sp, SupplyPointStatusTypes.R_AND_R_FACILITY)
    return "<span title='%d of %d'>%s%%</span>" % (r[1], r[2], floatformat(r[0]*100.0)) if r else "No data"

def _hrr_super(sp):
    r = historical_response_rate(sp, SupplyPointStatusTypes.SUPERVISION_FACILITY)
    return "<span title='%d of %d'>%s%%</span>" % (r[1], r[2], floatformat(r[0]*100.0)) if r else "No data"

def _hrr_soh(sp):
    r = historical_response_rate(sp, SupplyPointStatusTypes.SOH_FACILITY)
    return "<span title='%d of %d'>%s%%</span>" % (r[1], r[2], floatformat(r[0]*100.0)) if r else "No data"

def _dg_class(cell):
    if _dg(cell.object):
        return "width_10 delivery_group group_"+_dg(cell.object)
    else:
        return "width_10"

def _msd_class(cell):
    return "msd_code"

def _fac_name_class(cell):
    return "fac_name"

def _stock_class(cell):
    
    mos = historical_months_of_stock(cell.object, cell.column.product, cell.row.table.year, cell.row.table.month, -1)
    mos = float(mos)
    if mos == -1:
        return "insufficient_data"
    elif mos == 0.00:
        return "zero_count stock_iconified"
    elif mos < 1:
        return "low_stock stock_iconified"
    elif mos <= 3:
        return "adequate_stock stock_iconified"
    else:
        return "overstock stock_iconified"

class RandRReportingHistoryTable(MonthTable):
    code = Column()
    name = Column(name="Facility Name", value=lambda cell: cell.object.name, sort_key_fn=lambda obj: obj.name, link=supply_point_link)
    delivery_group = Column(css_class=_dg_class, value=lambda cell: _dg(cell.object), sort_key_fn=_dg, name="D G")

    submitted = RandRSubmittedColumn(name="R&R Submitted This Quarter",
                                     value=_randr_value,
                                     format="d M Y P",
                                     css_class=_randr_css_class,
                                     sortable=False)
    contact = Column(name="Contact", value=lambda cell: _default_contact(cell.object), sort_key_fn=_default_contact)
    lead_time = Column(sortable=False, name="Lead Time", value=lambda cell: calc_lead_time(cell.object, month=cell.row.table.month, year=cell.row.table.year))
    response_rate = Column(name="Historical Response Rate", safe=True, value=lambda cell: _hrr_randr(cell.object), sort_key_fn=lambda sp: historical_response_rate(sp, SupplyPointStatusTypes.R_AND_R_FACILITY))
    @property
    def submitting_group(self):
        return DeliveryGroups(self.month).current_submitting_group()

    class Meta:
        per_page = 9999
        order_by = ["D G", "Facility Name"]

class SupervisionTable(MonthTable):
    code = Column(value=lambda cell:cell.object.code, name="MSD Code", sort_key_fn=lambda obj: obj.code, titleized=False)
    name = Column(name="Facility Name", value=lambda cell: cell.object.name, sort_key_fn=lambda obj: obj.name, link=supply_point_link)
    delivery_group = Column(css_class=_dg_class, value=lambda cell: _dg(cell.object), sort_key_fn=_dg, name="D G")
    supervision_this_quarter = Column(sortable=False, name="Supervision This Quarter", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.SUPERVISION_FACILITY, "name"))
    date = DateColumn(sortable=False, value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.SUPERVISION_FACILITY, "status_date"))
    response_rate = Column(name="Historical Response Rate", safe=True, value=lambda cell: _hrr_super(cell.object), sort_key_fn=lambda sp: historical_response_rate(sp, SupplyPointStatusTypes.SUPERVISION_FACILITY))

    class Meta:
        per_page = 9999
        order_by = ["D G", "Facility Name"]


class ProductStockColumn(Column):
    def __init__(self, product, month, year):
        self.product = product
        super(ProductStockColumn, self).__init__(name=self.product.sms_code,
                                            value=lambda cell: historical_stock(cell.object,
                                                                                       self.product,
                                                                                       year,
                                                                                       month,
                                                                                       "No data"),
                                            sort_key_fn=lambda sp: historical_stock(sp,
                                                                                       self.product,
                                                                                       year,
                                                                                       month, -1),
                                            titleized=False,
                                            safe=True,
                                            css_class=_stock_class
       )

class ProductMonthsOfStockColumn(Column):
    def __init__(self, product, month, year):
        self.product = product
        super(ProductMonthsOfStockColumn, self).__init__(name=self.product.sms_code,
                                            value=lambda cell: historical_months_of_stock(cell.object,
                                                                                       self.product,
                                                                                       year,
                                                                                       month,
                                                                                       "No data"),
                                            sort_key_fn=lambda sp: historical_months_of_stock(sp,
                                                                                       self.product,
                                                                                       year,
                                                                                       month, -1),
                                            titleized=False,
                                            safe=True,
                                            css_class=_stock_class
       )

def _ontime_class(cell):
    state = soh_reported_on_time(cell.object, cell.row.table.year, cell.row.table.month)
    if state == OnTimeStates.LATE:
        return "last_reported warning_icon iconified"
    elif state == OnTimeStates.ON_TIME:
        return "last_reported good_icon iconified"

class StockOnHandTable(MonthTable):
    code = Column(value=lambda cell:cell.object.code, name="MSD Code", sort_key_fn=lambda obj: obj.code, titleized=False, css_class=_msd_class)
    name = Column(name="Facility Name", value=lambda cell: cell.object.name, sort_key_fn=lambda obj: obj.name, link=supply_point_link, css_class=_fac_name_class)
    delivery_group = Column(css_class=_dg_class, value=lambda cell: _dg(cell.object), sort_key_fn=_dg, name="D G")
    last_reported = Column(css_class=_ontime_class, value=lambda cell: last_report_span(cell.object, cell.row.table.year, cell.row.table.month, format=False))
    response_rate = Column(name="Hist. Resp. Rate", safe=True, value=lambda cell: _hrr_soh(cell.object), sort_key_fn=lambda sp: historical_response_rate(sp, SupplyPointStatusTypes.SOH_FACILITY))

    class Meta:
        per_page = 9999
        order_by = ["D G", "Facility Name"]

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