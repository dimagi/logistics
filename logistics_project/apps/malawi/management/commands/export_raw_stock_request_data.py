from __future__ import print_function
import csv
from django.db.models import Sum
from logistics_project.utils.dates import months_between
from datetime import datetime
from django.core.management.base import LabelCommand
from logistics.models import Product, SupplyPoint, StockRequest
from logistics_project.apps.malawi.util import fmt_pct
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData
from static.malawi import config


class Command(LabelCommand):
    help = "Exports a table of raw stock request data for generating lead time information"

    def handle(self, *args, **options):
        """
        Exports a table of stock status percentages with the following headings:
        product    district    facility    has    start date    end date    length
        """

        def _iter_rows():
            EXCEL_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
            def _parent(supply_point):
                return supply_point.supplied_by if supply_point else None

            def _display(supply_point):
                return supply_point.name if supply_point else '-'

            def _datestring(date):
                return date.strftime(EXCEL_DATE_FORMAT) if date else ''

            all_requests = StockRequest.objects.order_by('supply_point', 'requested_on', 'product')
            for req in all_requests:
                yield [
                    _display(_parent(_parent(req.supply_point))),
                    _display(_parent(req.supply_point)),
                    req.supply_point.name,
                    req.supply_point.code,
                    req.status,
                    _datestring(req.requested_on),
                    _datestring(req.responded_on),
                    _datestring(req.received_on),
                    req.product.name,
                ]

        if len(args) == 0:
            print('please specify a filename')
            return

        filename = args[0]
        f = file(filename, 'w')
        out = csv.writer(f)
        out.writerow([
            'district',
            'facility',
            'hsa name',
            'hsa code',
            'order status',
            'date requested',
            'date responded',
            'date received',
            'product',
        ])

        for i, row in enumerate(_iter_rows()):
            out.writerow(row)
