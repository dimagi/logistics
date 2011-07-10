from django.core.management.base import BaseCommand
from dimagi.utils.couch.database import get_db
from django.conf import settings
import sys
from logistics.apps.ewsghana import loader

class Command(BaseCommand):
    help = "Initialize static data for ghana"

    def handle(self, *args, **options):
        if len(args) != 1:
            print "Please specify the csv file from where to load facilities"
            return
        loader.AddFacilities(args[0])
