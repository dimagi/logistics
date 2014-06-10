import csv
from django.db.models import Sum
from dimagi.utils.dates import months_between
from datetime import datetime
from django.core.management.base import LabelCommand
from logistics_project.apps.malawi.util import get_facility_supply_points, fmt_pct
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData


CATEGORIES = [
    "without_stock",
    "under_stock",
    "good_stock",
    "over_stock",
    "without_data",
]


def _fmt_cat(category):
    return ' '.join(category.split('_'))


class Command(LabelCommand):
    help = "Exports a table of stock status percentages"

    def handle(self, *args, **options):
        """
        Exports a table of stock status percentages with the following headings:
        product    district    facility    has    start date    end date    length
        """

        def _get_row(window_date, facility):

            filtered = ProductAvailabilityData.objects.filter(
                supply_point=facility,
                date=window_date,
            )
            # stolen from stock status report
            ordered_slugs_managed = ['managed_and_%s' % slug for slug in CATEGORIES]
            values = filtered.aggregate(*[Sum(slug) for slug in ordered_slugs_managed + ['managed']])
            raw_vals = [values["managed_and_%s__sum" % k] or 0 for k in CATEGORIES]
            denom = values["managed__sum"] or 0
            pcts = [fmt_pct(val, denom) for val in raw_vals]

            def _parent(supply_point):
                return supply_point.supplied_by if supply_point else None

            def _display(supply_point):
                return supply_point.name if supply_point else '-'

            district = _parent(facility)
            EXCEL_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
            return [
                window_date.strftime(EXCEL_DATE_FORMAT),
                _display(district),
                _display(facility),
                facility.code,
            ] + [denom] + raw_vals + pcts

        if len(args) == 0:
            print 'please specify a filename'
            return

        filename = args[0]
        f = file(filename, 'w')
        out = csv.writer(f)
        out.writerow([
            'date',
            'district',
            'facility',
            'facility code',
            'total hsas',
        ] + ['hsas %s' % _fmt_cat(cat) for cat in CATEGORIES] + ['%% %s' % _fmt_cat(cat) for cat in CATEGORIES])


        start_date = datetime(2012, 1, 1)
        now = datetime.now()
        facs = get_facility_supply_points()

        for year, month in months_between(start_date, now):
            print 'getting data for %s-%s' % (month, year)
            window_date = datetime(year, month, 1)
            for fac in facs:
                out.writerow(_get_row(window_date, fac))
