from __future__ import print_function
from __future__ import unicode_literals
import csv
from django.db.models import Sum
from logistics_project.utils.dates import months_between
from datetime import datetime
from django.core.management.base import LabelCommand
from logistics.models import Product, SupplyPoint
from logistics_project.apps.malawi.util import get_facility_supply_points, fmt_pct
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData
from static.malawi import config


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
        products = Product.objects.all()

        def _get_rows(window_date, facility):
            initial = ProductAvailabilityData.objects.filter(
                supply_point=facility,
                date=window_date,
            )
            for p in products:
                filtered = initial.filter(product=p)
                if filtered.count():
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

                    EXCEL_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
                    yield [
                        window_date.strftime(EXCEL_DATE_FORMAT),
                        facility.type.name,
                        _display(_parent(facility)),
                        _display(facility),
                        facility.code,
                        p.name,
                    ] + [denom] + raw_vals + pcts

        if len(args) == 0:
            print('please specify a filename')
            return

        filename = args[0]
        f = file(filename, 'w')
        out = csv.writer(f)
        out.writerow([
            'date',
            'location type',
            'location parent',
            'location',
            'location code',
            'product',
            'total hsas',
        ] + ['hsas %s' % _fmt_cat(cat) for cat in CATEGORIES] + ['%% %s' % _fmt_cat(cat) for cat in CATEGORIES])


        start_date = datetime(2012, 1, 1)
        now = datetime.now()
        sites = SupplyPoint.objects.filter(
            active=True,
            type__code__in=[
                config.SupplyPointCodes.FACILITY,
                config.SupplyPointCodes.DISTRICT,
                config.SupplyPointCodes.COUNTRY,
            ]
        ).order_by('type__code')

        for year, month in months_between(start_date, now):
            print('getting data for %s-%s' % (month, year))
            window_date = datetime(year, month, 1)
            for site in sites:
                for row in _get_rows(window_date, site):
                    out.writerow(row)
