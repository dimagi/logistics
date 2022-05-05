from __future__ import unicode_literals

from celery.decorators import task

from logistics.models import SupplyPoint
from logistics_project.apps.malawi.warehouse.runner import update_historical_data_for_supply_point
from logistics_project.utils.parsing import string_to_datetime
from warehouse.runner import update_warehouse

@task
def update_warehouse_async(start_date=None, end_date=None, cleanup=False):
    """
    To asynchronously update the warehouse, e.g. from a view.
    """
    return update_warehouse(start_date, end_date, cleanup)


@task
def update_historical_data_for_supply_point_task(sp_id, start_str=None, end_str=None):
    """
    Intializes a given supply point's warehouse data for a given date range
    """
    start = string_to_datetime(start_str) if start_str else None
    end = string_to_datetime(end_str) if end_str else None
    return update_historical_data_for_supply_point(SupplyPoint.objects.get(id=sp_id), start, end)

