from __future__ import unicode_literals
from django.core.management.base import BaseCommand
from logistics.models import Product, SupplyPoint
from logistics_project.apps.malawi.warehouse.models import CalculatedConsumption
from warehouse.models import ReportRun
from logistics_project.apps.malawi.util import get_country_sp,\
    hsa_supply_points_below
from logistics_project.utils.dates import months_between
from datetime import datetime
from django.db.models.aggregates import Min
from logistics_project.apps.malawi.warehouse.runner import _aggregate

class Command(BaseCommand):
    help = "A single-use command to set the initial consumption values."

    def handle(self, *args, **options):
        all_products = Product.objects.all()
        run_record = ReportRun.objects.order_by('start_run')[0]
        hsas = SupplyPoint.objects.filter(active=True, type__code='hsa').order_by('id')
        place = get_country_sp()
        end = run_record.end
        relevant_hsas = hsa_supply_points_below(place.location)
        
        for p in all_products:
            # We have to use a special date range filter here, 
            # since the warehouse can update historical values
            # outside the range we are looking at
            agg = CalculatedConsumption.objects.filter(
                update_date__gte=run_record.start_run,
                supply_point__in=hsas
            ).aggregate(Min('date'))
            new_start = agg.get('date__min', None)
            if new_start:
                assert new_start <= end
                for year, month in months_between(new_start, end):
                    window_date = datetime(year, month, 1)
                    _aggregate(CalculatedConsumption, window_date, place, relevant_hsas,
                       fields=['calculated_consumption', 
                               'time_stocked_out',
                               'time_with_data',
                               'time_needing_data'],
                       additonal_query_params={"product": p})
            
