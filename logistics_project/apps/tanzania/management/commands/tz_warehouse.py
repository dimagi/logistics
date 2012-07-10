from django.core.management.base import LabelCommand
from logistics_project.apps.tanzania.reporting.run_reports2 import cleanup,\
    generate
from datetime import datetime

class Command(LabelCommand):
    
    help = "Run the data warehouse"
    args = ""
    label = ""
    

    def handle(self, *args, **options):
        print "Start time: %s" % datetime.now()
        # cleanup()
        generate()
        print "End time: %s" % datetime.now()