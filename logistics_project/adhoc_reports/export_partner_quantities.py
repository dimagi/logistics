import csv
from apps.malawi.util import hsa_supply_points_below
from logistics.models import *
from calendar import month_name
f = file('out.csv', 'w')
out = csv.writer(f)

partner_codes = StockTransfer.objects.exclude(giver_unknown__iregex='.* .*').values_list('giver_unknown', flat=True).distinct()
partner_codes = filter(lambda x: StockTransfer.objects.filter(giver_unknown=x).count() > 5, partner_codes)
products = Product.objects.order_by('sms_code')
months = [(2011, x) for x in range(4,13)]
months.append((2012,1))

for partner in partner_codes:
    out.writerow(['Partner: %s' % partner])
    header_row = []
    data_rows = [[] for p in products]
    for m in months:
        print "%s %s" % (partner, StockTransfer.objects.filter(giver_unknown=partner, closed_on__year=m[0], closed_on__month=m[1]).count())
        header_row.append("%s %s" % (month_name[m[1]], m[0]))
        ds = Location.objects.filter(type='district')
        header_row.extend([d.name for d in ds])
        header_row.append('')
        for p in enumerate(products):
            q = StockTransfer.objects.filter(product=p[1], giver_unknown=partner, closed_on__year=m[0], closed_on__month=m[1])
            data_rows[p[0]].append(p[1].name)
            for d in ds:
                ps = q.filter(receiver__in=hsa_supply_points_below(d))
                qq = ps.values_list('amount', flat=True)
                if len(qq):
                    data_rows[p[0]].append(sum(qq))
                else:
                    data_rows[p[0]].append('-')
            data_rows[p[0]].append('')
    out.writerow(header_row)
    out.writerows(data_rows)
    out.writerow([])

f.close()
