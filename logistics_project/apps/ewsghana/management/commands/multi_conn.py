from random import randint
import sys
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from dimagi.utils.couch.database import get_db
from dimagi.utils.dates import DateSpan
from rapidsms.contrib.locations.models import Location
from logistics_project.apps.ewsghana import loader
from logistics.models import SupplyPoint
from logistics.reports import ReportingBreakdown

class Command(BaseCommand):

    def handle(self, *args, **options):
        self.multiconn()
        
    def multiconn(self):
        from rapidsms.models import *
        backend = Backend.objects.get(name='message_tester')
        conns = Connection.objects.exclude(contact=None)
        for conn in conns:
            contact = conn.contact
            new_conn = Connection(backend=backend, 
                                  contact=contact, 
                                  identity="+233%s"%randint(555,10000000))
            new_conn.save()
