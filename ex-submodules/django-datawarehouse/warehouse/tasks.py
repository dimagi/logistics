from __future__ import unicode_literals
from celery.decorators import task
from warehouse.runner import update_warehouse

@task
def update_warehouse_async(start_date=None, end_date=None, cleanup=False):
    """
    To asynchronously update the warehouse, e.g. from a view.
    """
    return update_warehouse(start_date, end_date, cleanup)

