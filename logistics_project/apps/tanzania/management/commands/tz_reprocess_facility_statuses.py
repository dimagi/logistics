from django.core.management.base import LabelCommand
from warehouse.models import ReportRun
from datetime import datetime
from logistics.models import SupplyPoint, ProductReport
from rapidsms.contrib.messagelog.models import Message
from logistics_project.apps.tanzania.models import SupplyPointStatus
from logistics_project.apps.tanzania.reporting.run_reports import process_facility_statuses,\
    process_facility_product_reports, active_facilities_below
from logistics.const import Reports
from logistics_project.apps.tanzania.reporting.models import GroupSummary
from django.db.models.aggregates import Sum

class Command(LabelCommand):

    help = "recompute the GroupSummary models for all data in the system."

    def handle(self, *args, **options):
        running = ReportRun.objects.filter(complete=False)
        if running.count() > 0:
            raise Exception("Warehouse already running, will do nothing...")

        else:
            last_run = ReportRun.last_success()
            first_run = ReportRun.objects.filter(complete=True,
                                                 has_error=False).order_by("start")[0]

            start_date = first_run.start
            first_activity = Message.objects.order_by('date')[0].date
            if start_date < first_activity:
                start_date = first_activity

            end_date = last_run.end
            new_run = ReportRun.objects.create(start=start_date, end=end_date,
                                               start_run=datetime.utcnow())
        try:
            recompute(new_run)
        except:
            new_run.has_error = True
            raise
        finally:
            # complete run
            new_run.end_run = datetime.utcnow()
            new_run.complete = True
            new_run.save()
            print "End time: %s" % datetime.now()

def recompute(run_record):
    facilities = SupplyPoint.objects.filter(
        active=True,
        type__code='facility'
    ).order_by('id')
    count = facilities.count()
    for i, facility in enumerate(facilities):
        print "processing facility %s (%s) (%s of %s)" % (
            facility.name, str(facility.id), i+1, count
        )
        # first clear everything out
        clear_group_summaries(facility)

        # then update statuses like in the normal warehouse workflow
        new_statuses = SupplyPointStatus.objects.filter(
            supply_point=facility,
            status_date__gte=run_record.start,
            status_date__lt=run_record.end
        ).order_by('status_date')
        process_facility_statuses(facility, new_statuses, alerts=False)

        new_reports = ProductReport.objects.filter(
            supply_point=facility,
            report_date__gte=run_record.start,
            report_date__lt=run_record.end,
            report_type__code=Reports.SOH
        ).order_by('report_date')
        process_facility_product_reports(facility, new_reports)

    # aggregates
    non_facilities = SupplyPoint.objects.filter(active=True).exclude(type__code='facility').order_by('id')
    count = non_facilities.count()
    for i, org in enumerate(non_facilities):
        facs = list(active_facilities_below(org))
        print "processing non-facility %s (%s) (%s of %s)" % (
            org.name, str(org.id), i+1, count
        )
        
        for gsum in GroupSummary.objects.filter(org_summary__supply_point=org):
            sub_sums = GroupSummary.objects.filter(
                title=gsum.title,
                org_summary__date=gsum.org_summary.date,
                org_summary__supply_point__in=facs,
            )

            fields = ['total', 'responded', 'on_time', 'complete']
            totals = sub_sums.aggregate(*[Sum(f) for f in fields])
            [setattr(gsum, f, totals["%s__sum" % f] or 0) for f in fields]
            gsum.save()

def clear_group_summaries(supply_point):
    for gs in GroupSummary.objects.filter(org_summary__supply_point=supply_point):
        gs.total = 0
        gs.responded = 0
        gs.on_time = 0
        gs.complete = 0
        gs.save()
