from django.core.management.base import BaseCommand
from optparse import make_option
from logistics.models import SupplyPoint
import xlrd
import os


class Command(BaseCommand):
    help = "Update facilities code from excel file (usage in migration from ILS to HQ)"
    option_list = BaseCommand.option_list + (
        make_option('--test',
            action='store_true',
            dest='test',
            default=False,
            help='Delete poll instead of closing it'),
        )

    def handle(self, *args, **options):
        PATH = 'apps/tanzania/management/commands/resource'

        for file_name in os.listdir(PATH):
            print("Read %s" % file_name)
            xls_file = xlrd.open_workbook(os.path.join(PATH, file_name))
            for sheet in xls_file.sheets():
                print "Updates for district - %s" % sheet.name
                for cell in sheet._cell_values[1:]:
                    if cell[1] and cell[3]: # skip facilities which didn't exist in ILS
                        try:
                            sp = SupplyPoint.objects.filter(code=cell[1])[:1].get()
                            sp.code = cell[3]
                            sp.location.code = cell[3]
                            try:
                                ex_sp = SupplyPoint.objects.filter(code=cell[3])[:1].get()
                                if ex_sp.code != sp.code:
                                    print "Conflict in facilities: old_code - %s, new_code -%s, supply point id to update - %s, Conflicted supply point id - %s" % (cell[1], cell[3], sp.id, ex_sp.id)
                            except SupplyPoint.DoesNotExist:
                                if options['test']:
                                    print "Facility - DISTRICT_NAME: %s, ILS_CODE: %s, ILS_NAME %s, ELMIS_CODE: %s, ELMIS_NAME: %s - OK" % (sheet.name, cell[1], cell[0], cell[3], cell[2])
                                else:
                                    sp.location.save()
                                    sp.save()
                                pass
                        except SupplyPoint.DoesNotExist:
                            print("Problem with update facility: name - %s, code - %s" % (cell[0], cell[1]))
                            pass



