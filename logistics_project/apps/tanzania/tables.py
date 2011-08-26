from datetime import datetime
from djtables import Table, Column
from djtables.column import DateColumn
from logistics_project.apps.tanzania.models import SupplyPointStatusTypes, SupplyPointStatusValues
from utils import latest_status


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

def supply_point_link(cell):
    from logistics_project.apps.tanzania.views import tz_location_url
    return tz_location_url(cell.object.location)

class OrderingStatusTable(MonthTable):
    """
    Same as above but includes a column for the HSA
    """
    code = Column()
    delivery_group = Column(sortable=False, value=lambda cell: cell.object.groups.all()[0] if cell.object.groups.count() else None, name="Delivery Group")
    name = Column(link=supply_point_link)
    randr_status = Column(sortable=False, name="R&R Status", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.R_AND_R_FACILITY, "name"))
    randr_date = DateColumn(sortable=False, name="R&R Date", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.R_AND_R_FACILITY, "status_date"))
    delivery_status = Column(sortable=False, name="R&R Status", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.DELIVERY_FACILITY, "name"))
    delivery_date = DateColumn(sortable=False, name="R&R Date", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.DELIVERY_FACILITY, "status_date"))

    class Meta:
        order_by = '-code'

class RandRReportingHistoryTable(MonthTable):
    code = Column()
    name = Column(name="Facility Name", value=lambda cell:cell.object.name)
    submitted = Column(name="R&R Submitted This Quarter", value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.R_AND_R_FACILITY, "status_date", value=SupplyPointStatusValues.SUBMITTED))
    contact = Column(name="Contact", value=lambda cell: None)

class SupervisionTable(MonthTable):
    code = Column(value=lambda cell:cell.object.code, name="MSD Code")
    name = Column(name="Facility Name", value=lambda cell: cell.object.name)
    supervision_this_quarter = Column(value=lambda cell: _latest_status_or_none(cell, SupplyPointStatusTypes.SUPERVISION_FACILITY, "status_date"))
    date = DateColumn()

class StockOnHandTable(MonthTable):
    code = Column(value=lambda cell:cell.object.code, name="MSD Code")
    name = Column(name="Facility Name", value=lambda cell: cell.object.name)
    last_reported = Column()
    
