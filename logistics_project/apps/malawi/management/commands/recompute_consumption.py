from django.core.management.base import LabelCommand
from warehouse.models import ReportRun
from datetime import datetime
from logistics.models import SupplyPoint, Product
from logistics_project.apps.malawi.warehouse.models import CalculatedConsumption
from rapidsms.contrib.messagelog.models import Message
from dimagi.utils.dates import months_between
from logistics_project.apps.malawi.warehouse.runner import ReportPeriod,\
    update_consumption, aggregate, update_consumption_times
from logistics_project.apps.malawi.util import hsa_supply_points_below

class Command(LabelCommand):
    
    help = "recompute the CalculatedConsumption models for all data in the system."
    
    def handle(self, *args, **options):
        last_run = ReportRun.last_success()
        first_run = ReportRun.objects.filter(complete=True,
                                             has_error=False).order_by("start")[0]

        start_date = first_run.start
        first_activity = Message.objects.order_by('date')[0].date
        if start_date < first_activity:
            start_date = first_activity

        end_date = last_run.end

        running = ReportRun.objects.filter(complete=False)
        if running.count() > 0:
            raise Exception("Warehouse already running, will do nothing...")

        # start new run
        new_run = ReportRun.objects.create(start=start_date, end=end_date,
                                           start_run=datetime.utcnow())
        try:
            recompute(new_run)
        finally:
            # complete run
            new_run.end_run = datetime.utcnow()
            new_run.complete = True
            new_run.save()
            print "End time: %s" % datetime.now()

def recompute(run_record):
    hsas = SupplyPoint.objects.filter(active=True, type__code='hsa').order_by('id')
    count = hsas.count()
    for i, hsa in enumerate(hsas[:1]):
        print "processing hsa %s (%s) (%s of %s)" % (
            hsa.name, str(hsa.id), i+1, count
        )
        clear_calculated_consumption(hsa)
        for year, month in months_between(run_record.start, run_record.end):
            window_date = datetime(year, month, 1)
            report_period = ReportPeriod(hsa, window_date, run_record.start, run_record.end)
            update_consumption(report_period)

    update_consumption_times(run_record.start_run)

    # aggregates
    non_hsas = SupplyPoint.objects.filter(active=True).exclude(type__code='hsa').order_by('id')
    count = non_hsas.count()
    all_products = Product.objects.all()
    for i, place in enumerate(non_hsas[:1]):
        print "processing non-hsa %s (%s) (%s/%s)" % (
            place.name, str(place.id), i+1, count
        )
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
