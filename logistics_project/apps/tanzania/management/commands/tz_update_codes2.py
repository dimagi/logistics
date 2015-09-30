from collections import defaultdict
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from logistics.models import SupplyPoint
from django.db import transaction
import xlrd
import os


PATH = 'apps/tanzania/management/commands/resource/'


class Command(BaseCommand):
    help = "Update facilities code from excel file (usage in migration from ILS to HQ)"
    option_list = BaseCommand.option_list + (
        make_option('--test',
            action='store_true',
            dest='test',
            default=False,
            help="Just print out test information but don't actually migrate anything"),
        )

    def handle(self, *args, **options):
        if not args:
            raise CommandError("You have to provide directories with facilities codes e.g. "
                               "./manage.py tz_update_codes2")

        xls_file = xlrd.open_workbook(os.path.join(PATH, args[0]))
        worksheet = xls_file.sheet_by_index(0)

        with transaction.commit_on_success():
            for old_site_code, new_site_code, name in zip(worksheet.col(2), worksheet.col(3), worksheet.col(0))[1:]:
                old_site_code_value = old_site_code.value
                new_site_code_value = new_site_code.value

                if (not new_site_code_value or not old_site_code_value) or (new_site_code_value == old_site_code_value):
                    continue

                try:
                    supply_point = SupplyPoint.objects.get(code=old_site_code_value)
                    try:
                        sp = SupplyPoint.objects.get(code=new_site_code_value)
                        print u'Probably duplicated code {} ({})'.format(sp, new_site_code_value)
                    except SupplyPoint.DoesNotExist:
                        if not options['test']:
                            supply_point.code = new_site_code_value
                            supply_point.location.code = new_site_code_value
                            supply_point.location.save()
                            supply_point.save()

                        print u'Updated supply point {} ({}). Changed site code to {}'.format(
                            supply_point.name, supply_point.code, new_site_code_value
                        )
                except SupplyPoint.DoesNotExist:
                    try:
                        SupplyPoint.objects.get(code=new_site_code_value)
                        print u'Supply point with site code {} already updated'.format(old_site_code_value)
                    except SupplyPoint.DoesNotExist:
                        print u'Supply point with site code {} doesn\'t exist'.format(old_site_code_value)
