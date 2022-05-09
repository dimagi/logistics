from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from django.core.management.base import BaseCommand

from logistics_project.utils.parsing import string_to_datetime
from warehouse.models import ReportRun
from datetime import datetime
from logistics.models import SupplyPoint, Product
from logistics_project.apps.malawi.warehouse.models import CalculatedConsumption
from rapidsms.contrib.messagelog.models import Message
from logistics_project.utils.dates import months_between
from logistics_project.apps.malawi.warehouse.runner import ReportPeriod,\
    update_consumption, aggregate, update_consumption_times
from logistics_project.apps.malawi.util import hsa_supply_points_below
from static.malawi.config import BaseLevel, SupplyPointCodes


class Command(BaseCommand):
    
    help = "recompute the CalculatedConsumption models for all data in the system."

    def add_arguments(self, parser):
        parser.add_argument(
            '--aggregate',
            action='store_true',
            dest='aggregate_only',
            default=False,
            help='Cleanup the tables before starting the warehouse',
        )
        parser.add_argument(
            '--hsa',
            action='store',
            dest='hsa',
            default=None,
            help="Only run this for a single HSA",
        )
        parser.add_argument(
            '--facility',
            action='store',
            dest='facility',
            default=None,
            help="Only run this for a single facility",
        )
        parser.add_argument(
            '--start',
            action='store',
            dest='start',
            default=None,
            help="Explicit start date",
        )

    def handle(self, *args, **options):
        aggregate_only = options['aggregate_only']
        if options['hsa'] and options['facility']:
            raise Exception("Please only specify one of hsa or facility arguments!")

        start_time = datetime.now()
        running = ReportRun.objects.filter(complete=False)
        if running.count() > 0:
            raise Exception("Warehouse already running, will do nothing...")

        if aggregate_only:
            # resume from the last run
            new_run = ReportRun.objects.order_by('-start_run')[0]
            new_run.complete = False
            new_run.save()

        else:
            last_run = ReportRun.last_success()
            first_run = ReportRun.objects.filter(complete=True,
                                                 has_error=False).order_by("start")[0]

            if options['start']:
                start_date = string_to_datetime(options['start'])
            else:
                start_date = first_run.start
                first_activity = Message.objects.order_by('date')[0].date
                if start_date < first_activity:
                    start_date = first_activity

            end_date = last_run.end
            new_run = ReportRun.objects.create(start=start_date, end=end_date,
                                               start_run=datetime.utcnow())
        try:
            recompute(new_run, aggregate_only, hsa_code=options['hsa'], facility_code=options['facility'])
        finally:
            # complete run
            new_run.end_run = datetime.utcnow()
            new_run.complete = True
            new_run.save()
            print("End time: %s" % datetime.now())
            print(f'Duration {datetime.now() - start_time}')


def recompute(run_record, aggregate_only, hsa_code=None, facility_code=None):
    if not aggregate_only:
        hsas = SupplyPoint.objects.filter(active=True, type__code='hsa').order_by('id')
        if hsa_code:
            hsas = hsas.filter(code=hsa_code)
        if facility_code:
            hsas = hsas.filter(supplied_by__code=facility_code)

        count = hsas.count()
        for i, hsa in enumerate(hsas):
            print("processing hsa %s (%s) (%s of %s)" % (
                hsa.name, str(hsa.id), i+1, count
            ))
            clear_calculated_consumption(hsa)
            for year, month in months_between(run_record.start, run_record.end):
                window_date = datetime(year, month, 1)
                report_period = ReportPeriod(hsa, window_date, run_record.start, run_record.end)
                update_consumption(report_period, BaseLevel.HSA)

    update_consumption_times(run_record.start_run)

    # aggregates
    if hsa_code:
        non_hsas, count = get_affected_parents(hsa_code)
    elif facility_code:
        non_hsas, count = _get_parent_lineage(SupplyPoint.objects.get(code=facility_code))
    else:
        non_hsas = SupplyPoint.objects.filter(active=True).exclude(
            type__code__in=[SupplyPointCodes.HSA, SupplyPointCodes.ZONE],
        ).order_by('id')
        count = non_hsas.count()

    all_products = Product.objects.all()
    for i, place in enumerate(non_hsas):
        print("processing non-hsa %s (%s) (%s/%s)" % (
            place.name, str(place.id), i+1, count
        ))
        relevant_hsas = hsa_supply_points_below(place.location)
        for year, month in months_between(run_record.start, run_record.end):
            window_date = datetime(year, month, 1)
            for p in all_products:
                aggregate(CalculatedConsumption, window_date, place, relevant_hsas,
                   fields=['calculated_consumption', 
                           'time_stocked_out',
                           'time_with_data',
                           'time_needing_data'],
                   additonal_query_params={"product": p})


def clear_calculated_consumption(supply_point):
    for cc in CalculatedConsumption.objects.filter(supply_point=supply_point):
        for f in ['calculated_consumption', 'time_with_data',
                  'time_needing_data', 'time_stocked_out']:
            setattr(cc, f, 0)
        cc.save()


def get_affected_parents(hsa_code):
    hsa = SupplyPoint.objects.get(code=hsa_code, type__code='hsa')
    facility = hsa.supplied_by
    return _get_parent_lineage(facility)

def _get_parent_lineage(supply_point):
    lineage = [supply_point]
    while supply_point.supplied_by:
        supply_point = supply_point.supplied_by
        if supply_point.type_id != SupplyPointCodes.ZONE:
            lineage.append(supply_point)
    return lineage, len(lineage)
