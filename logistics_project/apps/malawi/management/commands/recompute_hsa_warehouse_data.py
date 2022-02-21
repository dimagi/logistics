from optparse import make_option
from django.core.management.base import LabelCommand
from logistics_project.utils.parsing import string_to_datetime
from warehouse.models import ReportRun
from logistics.models import SupplyPoint
from logistics_project.apps.malawi.warehouse.models import TimeTracker, OrderRequest, OrderFulfillment
from rapidsms.contrib.messagelog.models import Message
from logistics_project.apps.malawi.warehouse.runner import MalawiWarehouseRunner
from static.malawi.config import SupplyPointCodes


class Command(LabelCommand):

    help = "recompute the warehouse data for single hsa"
    option_list = LabelCommand.option_list + (
        make_option('--start',
                    action='store',
                    dest='start',
                    default=None,
                    help="Start date."),
    )

    def handle(self, *args, **options):
        hsa_code = args[0]
        hsa = SupplyPoint.objects.get(code=hsa_code)
        warehouse_runner = MalawiWarehouseRunner()
        # consumption needs to be dealt with separately
        warehouse_runner.skip_consumption = True

        first_activity = Message.objects.order_by('date')[0].date
        if options['start']:
            start = string_to_datetime(options['start'])
        else:
            start = ReportRun.objects.filter(complete=True, has_error=False).order_by('start')[0].start
            start = max([first_activity, start])
        end = ReportRun.last_success().end

        # cleanup additive warehouse data models
        TimeTracker.objects.filter(supply_point=hsa).delete()
        OrderRequest.objects.filter(supply_point=hsa).delete()
        OrderFulfillment.objects.filter(supply_point=hsa).delete()

        print 'updating data for %s from %s - %s' % (
            hsa, start, end,
        )
        # update
        warehouse_runner.update_base_level_data(hsa, start, end)
        for parent in hsa.get_parents():
            if parent.type_id != SupplyPointCodes.ZONE:
                print 'updating %s' % parent
                warehouse_runner.update_aggregated_data(parent, start, end, since=None)
