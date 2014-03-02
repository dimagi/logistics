from django.core.management.base import LabelCommand
from logistics_project.apps.malawi.util import get_facility_supply_points, get_district_supply_points


class Command(LabelCommand):

    def handle(self, *args, **options):
        for f in get_facility_supply_points():
            _anonymize(f, 'HC', save=False)
        for d in get_district_supply_points():
            _anonymize(d, 'District', save=False)

def _anonymize(supply_point, prefix, save=True):
    name = '%s %s' % (prefix, supply_point.code)
    print '%s --> %s' % (supply_point.name, name)
    supply_point.name = name
    if save:
        supply_point.save()
    if supply_point.location:
        supply_point.location.name = name
        if save:
            supply_point.location.save()
