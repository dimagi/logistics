from django.core.management.base import LabelCommand
from datetime import datetime
from dimagi.utils.modules import to_function
from django.conf import settings
from optparse import make_option
from dimagi.utils.parsing import string_to_datetime
from warehouse.models import ReportRun
from django.db import transaction

class Command(LabelCommand):
    
    help = "Run the data warehouse"
    args = "<start_date> <end_date>"
    label = ""
    option_list = LabelCommand.option_list + \
        (make_option('--cleanup', action='store_true', dest='cleanup', default=False,
            help='Cleanup the tables before starting the warehouse'),)

    

    def handle(self, *args, **options):
        print "Start time: %s" % datetime.now()
        classpath = settings.WAREHOUSE_RUNNER if hasattr(settings, "WAREHOUSE_RUNNER") \
            else "warehouse.runner.DemoWarehouseRunner"
        runner = to_function(classpath, failhard=True)()
        
        last_run = ReportRun.last_success()
        # use the passed in date, or the last run end, or the beginning of time,
        # in the order that they're available
        start_date = (datetime.min if not last_run else last_run.end ) \
            if len(args) < 1 else string_to_datetime(args[0]) 
        # use the passed in date, or right now
        end_date = datetime.utcnow() if len(args) < 2 else string_to_datetime(args[1]) 
        
        print "executing warehouse from %s, %s to %s" % (classpath, start_date.date(), end_date.date())
        if options["cleanup"]:
            runner.cleanup(start_date, end_date)
        
        running = ReportRun.objects.filter(complete=False)
        if running.count() > 0:
            print "Warehouse already running, will do nothing..."
            return
    
        # start new run
        new_run = ReportRun.objects.create(start=start_date, end=end_date,
                                           start_run=datetime.utcnow())
        try: 
            runner.generate(start_date, end_date)
        except Exception:
            # just in case something funky happened in the DB
            transaction.rollback()
            new_run.has_error = True
            raise
        finally:
            # complete run
            new_run.end_run = datetime.utcnow()
            new_run.complete = True
            new_run.save()
            print "End time: %s" % datetime.now()

        