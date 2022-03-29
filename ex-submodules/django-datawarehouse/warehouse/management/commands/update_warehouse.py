from __future__ import unicode_literals
from django.core.management.base import LabelCommand
from optparse import make_option
from logistics_project.utils.parsing import string_to_datetime
from warehouse import runner

class Command(LabelCommand):
    
    help = "Run the data warehouse"
    args = "<start_date> <end_date>"
    label = ""
    option_list = LabelCommand.option_list + \
        (make_option('--cleanup', action='store_true', dest='cleanup', default=False,
            help='Cleanup the tables before starting the warehouse'),)

    

    def handle(self, *args, **options):
        
        start_date = None if len(args) < 1 else string_to_datetime(args[0]) 
        end_date = None if len(args) < 2 else string_to_datetime(args[1]) 
        cleanup = options["cleanup"]
        return runner.update_warehouse(start_date, end_date, cleanup) 
