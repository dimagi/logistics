from __future__ import print_function
from __future__ import unicode_literals
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from logistics.models import SupplyPoint
from logistics_project.apps.malawi.warehouse.runner import update_historical_data_for_supply_point


class Command(BaseCommand):
    help = "Backfill dashboard models with empty/fake data. For use in development only."

    def add_arguments(self, parser):
        parser.add_argument(
            '--code',
            action='store',
            dest='supply_point_code',
            help='Supply point to update',
        )

    def handle(self, supply_point_code, **options):
        supply_points = SupplyPoint.objects.filter(active=True)
        if supply_point_code:
            supply_points = supply_points.filter(code=supply_point_code)
        now = datetime.utcnow()
        before = now - timedelta(days=93)
        for supply_point in supply_points:
            print(('backfilling ', supply_point))
            update_historical_data_for_supply_point(supply_point, before, now)
