from djtables import Table, Column
from djtables.column import DateColumn
from logistics_project.apps.tanzania.models import SupplyPointStatusTypes
from utils import latest_status

class OrderingStatusTable(Table):
    """
    Same as above but includes a column for the HSA
    """

# Commented out for now until we can get this working
#    month = None
#    year = None
    code = Column(value=lambda cell:cell.object.code)
    delivery_group = Column(value=lambda cell: cell.object.groups.all()[0] if cell.object.groups.count() else None, name="Delivery Group")
    name = Column()
    randr_status = Column(name="R&R Status", value=lambda cell: latest_status(cell.object,
                                                                              SupplyPointStatusTypes.R_AND_R_FACILITY).name \
                                                                              if latest_status(cell.object, SupplyPointStatusTypes.R_AND_R_FACILITY) else None)
    randr_date = DateColumn(name="R&R Date", value=lambda cell:latest_status(cell.object, SupplyPointStatusTypes.R_AND_R_FACILITY).status_date \
                                                                             if latest_status(cell.object, SupplyPointStatusTypes.R_AND_R_FACILITY) else None )
    delivery_status = Column(value=lambda cell: latest_status(cell.object, SupplyPointStatusTypes.DELIVERY_FACILITY).name \
                                                              if latest_status(cell.object, SupplyPointStatusTypes.DELIVERY_FACILITY) else None )
    delivery_date = DateColumn(value=lambda cell:latest_status(cell.object, SupplyPointStatusTypes.DELIVERY_FACILITY).status_date \
                                                               if latest_status(cell.object, SupplyPointStatusTypes.DELIVERY_FACILITY) else None )

    class Meta:
        order_by = '-code'