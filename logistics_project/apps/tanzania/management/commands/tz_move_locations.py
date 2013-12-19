import csv
from optparse import make_option
from logistics.models import SupplyPoint
from django.core.management.base import LabelCommand
from logistics_project.apps.tanzania.reporting.run_reports import default_start_date, process_non_facility_warehouse_data
from warehouse.models import ReportRun


class Command(LabelCommand):
    help = "For a given list of locations, move them from one parent to another, if necessary."
    option_list = LabelCommand.option_list + (
        make_option('--dryrun', action='store_true', dest='dryrun', help='Dry run', default=False),
        make_option('--strict', action='store_true', dest='strict', help='Strict', default=False),

    )

    def handle(self, *args, **options):
        strict = options['strict']
        dryrun = options['dryrun']
        parents = set()
        warehouse_start_date = default_start_date()
        warehouse_end_date = ReportRun.last_success().end
        data_file = args[0]

        def _clean(string):
            # remove excess spaces from a string
            while "  " in string:
                string = string.replace('  ', ' ')
            return string.strip()

        with open(data_file, 'r') as f:
            reader = csv.reader(f)
            first = True
            for row in reader:
                if first:
                    first = False
                    continue

                name, active, code, parent, new_parent_name = row[:5]
                new_parent_name = new_parent_name.replace(' - ', '-').replace(' ', '-')
                fac = SupplyPoint.objects.get(code=code)
                new_parent = SupplyPoint.objects.get(code__iexact=new_parent_name)
                if strict:
                    assert fac.supplied_by.name == parent

                assert _clean(fac.name) == name, 'expected %s but was %s' % (fac.name, name)
                assert fac.location.parent == fac.supplied_by.location
                assert fac.type.code == 'facility'
                assert new_parent.type.code != 'facility'
                if fac.supplied_by == new_parent:
                    print 'already set %s' % fac
                else:
                    print '%s, %s --> %s' % (fac, fac.supplied_by, new_parent)
                    fac.supplied_by = new_parent
                    fac.location.parent = new_parent.location
                    fac.name = name
                    parents.update((fac.supplied_by, new_parent))
                    if not dryrun:
                        fac.save()

        if not dryrun:
            for parent in parents:
                # for all affected parents, rerun the aggregate warehouse update
                process_non_facility_warehouse_data(parent, warehouse_start_date, warehouse_end_date, strict=False)
