from __future__ import print_function
from __future__ import unicode_literals
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from logistics.models import SupplyPoint
from logistics_project.apps.malawi.warehouse.runner import update_historical_data_for_supply_point


class Command(BaseCommand):
    help = "Backfill dashboard models with empty/fake data. For use in development only."

    def handle(self, *args, **options):
        now = datetime.utcnow()
        before = now - timedelta(days=93)
        for supply_point in SupplyPoint.objects.filter(active=True):
            print(('backfilling ', supply_point))
            update_historical_data_for_supply_point(supply_point, before, now)
