from django.core.management.base import BaseCommand
from optparse import make_option
from django.db.models.query_utils import Q
from logistics.models import SupplyPoint
import xlrd
import os


class Command(BaseCommand):
    help = "Fix for improperly updated mbeya zone codes"
    option_list = BaseCommand.option_list + (
        make_option(
            '--test',
            action='store_true',
            dest='test',
            default=False,
            help="Just print out test information but don't actually migrate anything"
        ),
    )

    def handle(self, *args, **options):
        xls_file = xlrd.open_workbook(
            os.path.join(
                'apps/tanzania/management/commands/resource/part2',
                'ILSGateway-eLMIS facilities Mbeya Zone.xlsx'
            )
        )
        for sheet in xls_file.sheets():
            print "Updates for district - %s" % sheet.name
            for cell in sheet._cell_values[1:]:
                # only touch facilities which exist in ILS
                if cell[1] and cell[3]:
                    try:
                        sp = SupplyPoint.objects.filter(Q(code=cell[3]) | Q(code=cell[1]))[:1].get()
                        sp.code = cell[2]
                        sp.location.code = cell[2]
                        try:
                            ex_sp = SupplyPoint.objects.filter(code=cell[2])[:1].get()
                            if ex_sp.code != sp.code:
                                print "Conflict in facilities: old_code - %s, new_code -%s, supply point id to update - %s, Conflicted supply point id - %s" % (cell[1], cell[2], sp.id, ex_sp.id)
                        except SupplyPoint.DoesNotExist:
                            if options['test']:
                                print "Facility - DISTRICT_NAME: %s, ILS_CODE: %s, ILS_NAME %s, ELMIS_CODE: %s, ELMIS_NAME: %s - OK" % (sheet.name, cell[1], cell[0], cell[2], cell[3])
                            else:
                                sp.location.save()
                                sp.save()
                    except SupplyPoint.DoesNotExist:
                        print("Facility was not found in ILSGateway: name - %s, code - %s" % (cell[0], cell[1]))
