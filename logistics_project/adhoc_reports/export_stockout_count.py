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

header_row = []
data_rows = [[] for p in products]
for m in months:
    header_row.append("%s %s" % (month_name[m[1]], m[0]))
    ds = Location.objects.filter(type='district')
    header_row.extend([d.name for d in ds])
    header_row.append('')

    for p in enumerate(products):
        q = ProductReport.objects.filter(quantity=0, report_date__month=m[1], report_date__year=m[0], product=p[1])
        data_rows[p[0]].append(p[1].name)
        for d in ds:
            ps = q.filter(supply_point__in=hsa_supply_points_below(d))
            if len(ps):
                data_rows[p[0]].append(len(ps))
            else:
                data_rows[p[0]].append('0')
        data_rows[p[0]].append('')

out.writerow(header_row)
out.writerows(data_rows)
out.writerow([])

f.close()
