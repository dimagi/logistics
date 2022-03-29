from __future__ import print_function
from builtins import object
from datetime import datetime
from logistics_project.utils.modules import to_function
from django.conf import settings
from warehouse.models import ReportRun
from django.db import transaction
from django.db.utils import DatabaseError


class WarehouseRunner(object):
    """
    This class gets executed by the warehouse management command.
    Subclasses control how data gets into the warehouse.
    """
    
    def cleanup(self, start, end):
        """
        Cleanup all warehouse data between start and end.
        """
        pass
    
    def generate(self, run_record):
        """
        Generate all warehouse data between start and end.
        """
        pass
    
class DemoWarehouseRunner(WarehouseRunner):
    """
    A reference implementation of the warehouse runner. Your subclasses
    should probably do more than this.
    """
    
    def cleanup(self, start, end):
        print ("Demo warehouse cleanup! Would clean all data from %s-%s. "
               "Override WAREOUSE_RUNNER in your settings.py file to have "
               "this actually do something.") 
    
    def generate(self, run_record):
        print(("Demo warehouse generate! Would create all data from %s-%s. "
               "Override WAREOUSE_RUNNER in your settings.py file to have "
               "this actually do something.") % (run_record.start, run_record.end))
    

def get_warehouse_runner():
    """
    Get the configured runner, bsed on the WAREHOUSE_RUNNER setting, or
    the default demo runner if none found. 
    """
    classpath = settings.WAREHOUSE_RUNNER if hasattr(settings, "WAREHOUSE_RUNNER") \
        else "warehouse.runner.DemoWarehouseRunner"
    return to_function(classpath, failhard=True)()
    
def update_warehouse(start_date=None, end_date=None, cleanup=False):
    
    print("Start time: %s" % datetime.now())
    
    last_run = ReportRun.last_success()
    # use the passed in date, or the last run end, or the beginning of time,
    # in the order that they're available
    if start_date is None:
        start_date = (datetime.min if not last_run else last_run.end )
    # use the passed in date, or right now
    if end_date is None:
        end_date = datetime.utcnow() 
    
    runner = get_warehouse_runner()
    print("executing warehouse from %s, %s to %s" % (runner, start_date.date(), end_date.date()))
    if cleanup:
        runner.cleanup(start_date, end_date)
    
    running = ReportRun.objects.filter(complete=False)
    if running.count() > 0:
        raise Exception("Warehouse already running, will do nothing...")
        
    # start new run
    new_run = ReportRun.objects.create(start=start_date, end=end_date,
                                       start_run=datetime.utcnow())
    try: 
        runner.generate(new_run)
    except Exception as e:
        # just in case something funky happened in the DB
        if isinstance(e, DatabaseError):
            try:
                transaction.rollback()
            except:
                pass
        new_run.has_error = True
        raise
    finally:
        # complete run
        new_run.end_run = datetime.utcnow()
        new_run.complete = True
        new_run.save()
        print("End time: %s" % datetime.now())

