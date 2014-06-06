import csv
from logistics.models import StockTransaction
from datetime import datetime
from django.core.management.base import LabelCommand


class Command(LabelCommand):
    help = "Exports a table of all stockouts ever"

    def handle(self, *args, **options):
        """
        Exports a table of all stockouts ever with the following headings:
        product    district    facility    has    start date    end date    length
        """
        END_DATE = datetime.utcnow()
        EXCEL_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

        def _is_stockout(trans):
            if trans.ending_balance < 0:
                print 'negative balance!! %s, %s' % (trans.pk, trans)
            return trans.ending_balance == 0
        def _is_match(start_trans, end_trans):
            return (start_trans.supply_point == end_trans.supply_point and
                    start_trans.product == end_trans.product)

        def _get_row(start, end):
            if end is not None:
                assert start.date < end.date
                assert start.supply_point == end.supply_point
                assert start.product == end.product
                enddate = end.date
            else:
                enddate = END_DATE

            def _parent(supply_point):
                return supply_point.supplied_by if supply_point else None
            def _display(supply_point):
                return supply_point.name if supply_point else '-'

            facility = _parent(start.supply_point)
            district = _parent(facility)

            return [
                start.product.name,
                _display(district),
                _display(facility),
                _display(start.supply_point),
                start.supply_point.code,
                start.date.strftime(EXCEL_DATE_FORMAT),
                enddate.strftime(EXCEL_DATE_FORMAT),
                enddate == END_DATE,
                (enddate - start.date).days,
                (enddate - start.date).seconds,
            ]

        def _write_row(outfile, period_start, trans):
            row = _get_row(period_start, trans)
            if row:
                outfile.writerow(row)

        if len(args) == 0:
            print 'please specify a filename'
            return
        filename = args[0]
        f = file(filename, 'w')
        out = csv.writer(f)
        out.writerow(['Product', 'District', 'Facility', 'HSA', 'HSA Code', 'Start Date', 'End Date',
                      'Ongoing', 'Duration (days)', 'Duration (seconds)'])
        transactions = StockTransaction.objects.order_by('product', 'supply_point', 'date')
        count = StockTransaction.objects.count()
        period_start = None

        i = 0
        for trans in transactions:
            if period_start is None:
                if _is_stockout(trans):
                    # new period
                    period_start = trans
                else:
                    # nothing to do
                    pass
            elif _is_match(period_start, trans):
                # still in the same period, check if still stocked out or period is ending
                if _is_stockout(trans):
                    # nothing to do
                    pass
                else:
                    _write_row(out, period_start, trans)
                    period_start = None
            else:
                # we ran out of matches, just end it with the current date
                _write_row(out, period_start, None)
                period_start = None

            i += 1
            if i % 500 == 0:
                print 'processed %s/%s transactions' % (i, count)
