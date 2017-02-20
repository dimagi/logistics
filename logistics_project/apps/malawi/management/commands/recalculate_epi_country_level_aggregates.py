from datetime import datetime
from django.core.management.base import BaseCommand
from logistics.models import SupplyPoint
from logistics_project.apps.malawi.warehouse.runner import MalawiWarehouseRunner
from static.malawi.config import BaseLevel, SupplyPointCodes


class Command(BaseCommand):
    help = "Recalculates country-level aggregates for EPI"

    def handle(self, *args, **options):
        country = SupplyPoint.objects.get(type__code=SupplyPointCodes.COUNTRY)
        MalawiWarehouseRunner().update_aggregated_data(
            country,
            datetime(2016, 11, 1),
            datetime(2017, 2, 1),
            datetime(2016, 11, 1),
            base_level=BaseLevel.FACILITY
        )
