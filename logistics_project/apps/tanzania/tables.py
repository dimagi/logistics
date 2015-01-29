from datetime import datetime, timedelta
from django.core.urlresolvers import reverse
from django.template.defaultfilters import floatformat
from django.utils.functional import curry
from djtables import Table, Column
from djtables.column import DateColumn
from logistics_project.apps.tanzania.models import SupplyPointStatusTypes, SupplyPointStatusValues,\
    DeliveryGroups, OnTimeStates
from logistics_project.apps.tanzania.templatetags.tz_tags import last_report_span, last_report_cell
from logistics_project.apps.tanzania.utils import calc_lead_time, historical_response_rate, soh_reported_on_time, avg_past_lead_time
from logistics.models import SupplyPoint
from utils import latest_status
from rapidsms.models import Contact
from django.template import defaultfilters
from django.utils.translation import ugettext as _
from logistics.templatetags.logistics_report_tags import historical_stock, historical_months_of_stock
from logistics_project.apps.tanzania.reporting.models import *


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

def get_avg_lead_time(cell):
    date = datetime(cell.row.table.year, cell.row.table.month,1)
    org_sum = OrganizationSummary.objects.filter(supply_point=cell.object, date=date)
    if org_sum:
        if org_sum[0].average_lead_time_in_days:
            return org_sum[0].average_lead_time_in_days
    return "None"

def get_this_lead_time(cell):
    lead_time = calc_lead_time(cell.object, month=cell.row.table.month, year=cell.row.table.year)
    if lead_time and lead_time > timedelta(days=30) and lead_time < timedelta(days=100):
        return '%.1f' % lead_time.days
    return "None"

def get_historical_response_rate(cell, title):
    total_responses = 0
    total_possible = 0
    end_date = datetime(cell.row.table.year, cell.row.table.month, 1)

    for g in GroupSummary.objects.filter(org_summary__supply_point=cell.object, title=title,
                org_summary__date__lte=end_date):
        if g:
            total_responses += g.responded
            total_possible += g.total
    if total_possible:
        return "%.1f%%" % (100.0 * total_responses / total_possible)
    return "None"

def supply_point_link(cell):
    from logistics_project.apps.tanzania.views import tz_location_url
    return tz_location_url(cell.object.location)

def msg_supply_point_link(cell):
    from logistics_project.apps.tanzania.views import tz_location_url
    return tz_location_url(cell.object.contact.supply_point.location)

def reports_link(cell, report_name):
    return "%s?place=%s&year=%s&month=%s" % (reverse('new_reports', args=(report_name,)), cell.object.location.code, cell.row.table.year, cell.row.table.month)

class RandRStatusTable(MonthTable):
    """
    Same as above but includes a column for the HSA
    """
    code = Column()
    name = Column(name="Facility Name", value=lambda cell: cell.object.name, sort_key_fn=lambda obj: obj.name, link=supply_point_link)
#    delivery_group = Column(value=lambda cell: _dg(cell.object), sort_key_fn=_dg, name="D G")
    randr_status = Column(sortable=False, name="R&R Status", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.R_AND_R_FACILITY, "name"))
    randr_date = DateColumn(sortable=False, name="R&R Date", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.R_AND_R_FACILITY, "status_date"))
    
    class Meta:
        per_page = 9999
        order_by = ["Facility Name"]

class DeliveryStatusTable(MonthTable):
    """
    Same as above but includes a column for the HSA
    """
    code = Column()
    name = Column(name="Facility Name", value=lambda cell: cell.object.name, sort_key_fn=lambda obj: obj.name, link=supply_point_link)
    delivery_status = Column(sortable=False, name="Delivery Status", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.DELIVERY_FACILITY, "name"))
    delivery_date = DateColumn(sortable=False, name="Delivery Date", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.DELIVERY_FACILITY, "status_date"))
    last_lead_time = Column(sortable=False, name="Last Lead Time", value=lambda cell: calc_lead_time(cell.object, month=cell.row.table.month, year=cell.row.table.year))
    average_lead_time = Column(sortable=False, name="Average Lead Time in Days", value=lambda cell: avg_past_lead_time(cell.object))

    class Meta:
        per_page = 9999
        order_by = ["Facility Name"]

class DeliveryStatusTable2(MonthTable):
    """
    Same as above but includes a column for the HSA
    """
    code = Column()
    name = Column(name="Facility Name", value=lambda cell: cell.object.name, sort_key_fn=lambda obj: obj.name, link=supply_point_link)
    delivery_status = Column(sortable=False, name="Delivery Status", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.DELIVERY_FACILITY, "name"))
    delivery_date = DateColumn(sortable=False, name="Delivery Date", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.DELIVERY_FACILITY, "status_date"))
    last_lead_time = Column(sortable=False, name="This Cycle Lead Time", value=lambda cell: get_this_lead_time(cell))
    average_lead_time = Column(sortable=False, name="Average Lead Time in Days", value=lambda cell: get_avg_lead_time(cell))

    class Meta:
        per_page = 9999
        order_by = ["Facility Name"]

class RandRSubmittedColumn(DateColumn):
    # copied and modified from djtables DateColumn

    def render(self, cell):
        val = self.value(cell)
        if val:
            return super(RandRSubmittedColumn, self).render(cell)
        else:
            return _("Not reported")

def _randr_value(cell):
    latest_submit = _latest_status_or_none(cell, SupplyPointStatusTypes.R_AND_R_FACILITY, "status_date", value=SupplyPointStatusValues.SUBMITTED)
    latest_not_submit = _latest_status_or_none(cell, SupplyPointStatusTypes.R_AND_R_FACILITY, "status_date", value=SupplyPointStatusValues.NOT_SUBMITTED)
    if latest_submit:
        return latest_submit 
    else:
        return latest_not_submit

def _randr_css_class(cell):
    latest_submit = _latest_status_or_none(cell, SupplyPointStatusTypes.R_AND_R_FACILITY, "status_date", value=SupplyPointStatusValues.SUBMITTED)
    latest_not_submit = _latest_status_or_none(cell, SupplyPointStatusTypes.R_AND_R_FACILITY, "status_date", value=SupplyPointStatusValues.NOT_SUBMITTED)
    if latest_submit:
        return "good_icon iconified"
    else:
        return "warning_icon iconified"

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
    NO_DATA = -1
    STOCKOUT = 0.00
    LOW = 3
    ADEQUATE = 6

    mos = historical_months_of_stock(cell.object, cell.column.product, cell.row.table.year, cell.row.table.month, -1)
    mos = float(mos)
    if not cell.object.supplies_product(cell.column.product) or mos == NO_DATA:
        return "insufficient_data prod-%s" % cell.column.product.sms_code
    elif mos == STOCKOUT:
        return "zero_count stock_iconified prod-%s" % cell.column.product.sms_code
    elif mos < LOW:
        return "low_stock stock_iconified prod-%s" % cell.column.product.sms_code
    elif mos <= ADEQUATE:
        return "adequate_stock stock_iconified prod-%s" % cell.column.product.sms_code
    else:
        return "overstock stock_iconified prod-%s" % cell.column.product.sms_code

def _prod_class(cell):
    return "prod-%s" % cell.column.product.sms_code

class RandRReportingHistoryTable_old(MonthTable):
    code = Column()
    name = Column(name="Facility Name", value=lambda cell: cell.object.name, sort_key_fn=lambda obj: obj.name, link=supply_point_link)
    submitted = RandRSubmittedColumn(name="R&R Status",
                                     value=_randr_value,
                                     format="d M Y",
                                     css_class=_randr_css_class,
                                     sortable=False)
    contact = Column(name="Contact", value=lambda cell: _default_contact(cell.object), sort_key_fn=_default_contact)
    response_rate = Column(name="Historical Response Rate", safe=True, value=lambda cell: _hrr_randr(cell.object), sort_key_fn=lambda sp: historical_response_rate(sp, SupplyPointStatusTypes.R_AND_R_FACILITY))
    @property
    def submitting_group(self):
        return DeliveryGroups(self.month).current_submitting_group()

    class Meta:
        per_page = 9999
        order_by = ["Facility Name"]

class RandRReportingHistoryTable(MonthTable):
    code = Column()
    name = Column(name="Facility Name", value=lambda cell: cell.object.name, sort_key_fn=lambda obj: obj.name, link=supply_point_link)
    submitted = RandRSubmittedColumn(name="R&R Status",
                                     value=_randr_value,
                                     format="d M Y",
                                     css_class=_randr_css_class,
                                     sortable=False)
    contact = Column(name="Contact", value=lambda cell: _default_contact(cell.object), sort_key_fn=_default_contact)
    response_rate = Column(name="Historical Response Rate", safe=True, value=lambda cell: get_historical_response_rate(cell,'rr_fac'), sort_key_fn=lambda sp: historical_response_rate(sp, SupplyPointStatusTypes.R_AND_R_FACILITY))
    @property
    def submitting_group(self):
        return DeliveryGroups(self.month).current_submitting_group()

    class Meta:
        per_page = 9999
        order_by = ["Facility Name"]


class SupervisionTable_old(MonthTable):
    code = Column(value=lambda cell:cell.object.code, name="MSD Code", sort_key_fn=lambda obj: obj.code, titleized=False)
    name = Column(name="Facility Name", value=lambda cell: cell.object.name, sort_key_fn=lambda obj: obj.name, link=supply_point_link)
    supervision_this_quarter = Column(sortable=False, name="Supervision This Quarter", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.SUPERVISION_FACILITY, "name"))
    date = DateColumn(sortable=False, value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.SUPERVISION_FACILITY, "status_date"))
    response_rate = Column(name="Historical Response Rate", safe=True, value=lambda cell: _hrr_super(cell.object), sort_key_fn=lambda sp: historical_response_rate(sp, SupplyPointStatusTypes.SUPERVISION_FACILITY))

    class Meta:
        per_page = 9999
        order_by = ["Facility Name"]


class SupervisionTable(MonthTable):
    code = Column(value=lambda cell:cell.object.code, name="MSD Code", sort_key_fn=lambda obj: obj.code, titleized=False)
    name = Column(name="Facility Name", value=lambda cell: cell.object.name, sort_key_fn=lambda obj: obj.name, link=supply_point_link)
    supervision_this_quarter = Column(sortable=False, name="Supervision This Quarter", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.SUPERVISION_FACILITY, "name"))
    date = DateColumn(sortable=False, value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.SUPERVISION_FACILITY, "status_date"))
    response_rate = Column(name="Historical Response Rate", safe=True, value=lambda cell: get_historical_response_rate(cell,'super_fac'), sort_key_fn=lambda sp: historical_response_rate(sp, SupplyPointStatusTypes.SUPERVISION_FACILITY))

    class Meta:
        per_page = 9999
        order_by = ["Facility Name"]


class ProductStockColumn(Column):
    def historical_stock_display(self, supply_point, product, year, month, default_value="No data"):
        # there are some products marked as not supplied that have data
        # so shouldn't hide that
        historical_value = historical_stock(supply_point, product, year, month, default_value)
        if not supply_point.supplies(product) and historical_value == 0:
            return default_value
        else:
            return historical_value

    def __init__(self, product, month, year):
        self.product = product
        super(ProductStockColumn, self).__init__(
            name=self.product.sms_code,
            value=lambda cell: self.historical_stock_display(
                cell.object,
                self.product,
                year,
                month,
                "No data"
            ),
            sort_key_fn=lambda sp: historical_stock(
                sp,
                self.product,
                year,
                month,
                -1
            ),
            titleized=False,
            safe=True,
            css_class=_stock_class,
            header_class="prod-%s" % product.sms_code
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
                                            css_class=_stock_class,
                                            header_class = "prod-%s" % product.sms_code
       )

class AggregateStockoutPercentColumn(Column):
    def __init__(self, product, month, year):
        self.product = product
        super(AggregateStockoutPercentColumn, self).__init__(#name=self.product.sms_code,
                                            value=lambda cell: cell.object.breakdown.percent_stocked_out(self.product, year, month),
                                            sort_key_fn=lambda obj: object.breakdown.percent_stocked_out(self.product, year, month),
                                            name="%s stock outs this month" % product.sms_code,
                                            titleized=False,
                                            safe=True,
                                            css_class=_prod_class,
                                            header_class = "prod-%s" % product.sms_code

       )

class AggregateStockoutPercentColumn2(Column):
    def __init__(self, product, percent):
        self.product = product
        super(AggregateStockoutPercentColumn2, self).__init__(#name=self.product.sms_code,
                                            value=lambda cell: percent,
                                            sort_key_fn=lambda obj: percent,
                                            name="%s stock outs this month" % product.sms_code,
                                            titleized=False,
                                            safe=True,
                                            css_class=_prod_class,
                                            header_class = "prod-%s" % product.sms_code

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

class AggregateRandRTable(MonthTable):
    name = Column(value=lambda cell: cell.object.name, sort_key_fn=lambda object: object.name, link=lambda cell: reports_link(cell, 'randr'))
    percent_on_time = Column(sortable=False, value=lambda cell: cell.object.breakdown.percent_randr_on_time(), name="% Facilities Submitting R&R On Time", safe=True)
    percent_late = Column(sortable=False, value=lambda cell: cell.object.breakdown.percent_randr_late(), name="% Facilities Submitting R&R Late", safe=True)
    percent_not_submitted = Column(sortable=False, value=lambda cell: cell.object.breakdown.percent_randr_not_submitted(), name="% Facilities with R&R Not Submitted", safe=True)
    percent_not_responding = Column(sortable=False, value=lambda cell: cell.object.breakdown.percent_randr_not_responding(), name="% Facilities Not Responding to R&R Reminder", safe=True)
    historical_response_rate = Column(sortable=False, value=lambda cell: cell.object.breakdown.randr_response_rate(), name = "Historical Response Rate", safe=True)

    class Meta:
        per_page = 9999

class AggregateSOHTable(MonthTable):
    name = Column(value=lambda cell: cell.object.name, sort_key_fn=lambda object: object.name, link=lambda cell:reports_link(cell, 'soh'))
    percent_on_time = Column(sortable=False, value=lambda cell: cell.object.breakdown.percent_soh_on_time(), name="% Facilities Submitting SOH On Time", safe=True)
    percent_late = Column(sortable=False, value=lambda cell: cell.object.breakdown.percent_soh_late(), name="% Facilities Submitting SOH Late", safe=True)
    percent_not_responding = Column(sortable=False, value=lambda cell: cell.object.breakdown.percent_soh_not_responding(), name="% Facilities Not Responding to SOH", safe=True)
    percent_with_stockouts = Column(sortable=False, value=lambda cell: cell.object.breakdown.percent_stockouts_in_month(), name="% Facilities with 1 or More Stockouts This Month", safe=True)

    class Meta:
        per_page = 9999
    
class AggregateSupervisionTable(MonthTable):
    name = Column(value=lambda cell: cell.object.name, sort_key_fn=lambda object: object.name, link=lambda cell:reports_link(cell, 'supervision'))
    percent_received = Column(sortable=False, value=lambda cell: cell.object.breakdown.percent_supervision_received(), name="% Supervision Received", safe=True)
    percent_not_received = Column(sortable=False, value=lambda cell: cell.object.breakdown.percent_supervision_not_received(), name="% Supervision Not Received", safe=True)
    percent_not_responding = Column(sortable=False, value=lambda cell: cell.object.breakdown.percent_supervision_not_responding(), name="% Supervision Not Responding", safe=True)
    historical_response_rate = Column(sortable=False, value=lambda cell: cell.object.breakdown.supervision_response_rate(), name = "Historical Response Rate", safe=True)

    class Meta:
        per_page = 9999


class LeadTimeTable(MonthTable):
    name = Column(value=lambda cell: cell.object.name, sort_key_fn=lambda object: object.name, link=lambda cell:reports_link(cell, 'delivery'))
    average_lead_time = Column(sortable=False, value=lambda cell: cell.object.breakdown.avg_lead_time, name="Average Lead Time in Days", safe=True)

    class Meta:
        per_page = 9999


class UnrecognizedMessagesTable(Table):
    code = Column(value=lambda cell:cell.object.contact.supply_point.code, name="MSD Code", sort_key_fn=lambda obj: obj.supply_point.code, titleized=False, css_class=_msd_class)
    facility = Column(value=lambda cell: cell.object.contact.supply_point.name, link=msg_supply_point_link)
    contact = Column(sortable=False, value=lambda cell: cell.object.contact.name)
    date = DateColumn(format="H:i M d")
    text = Column()
