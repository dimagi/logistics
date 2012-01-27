import csv
from apps.malawi.util import hsa_supply_points_below
from logistics.models import *
from calendar import month_name
from django.db.models.expressions import F
f = file('overstock_avg.csv', 'w')
out = csv.writer(f)

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
        q = StockRequest.objects.filter(status='received', amount_requested__lt=F('amount_received'), product=p[1], received_on__month=m[1], received_on__year=m[0])
        data_rows[p[0]].append(p[1].name)
        for d in ds:
            ps = q.filter(supply_point__in=hsa_supply_points_below(d)).values_list('amount_requested', 'amount_received')
            if len(ps):
                ps = "%.2f" % (sum(map(lambda x: abs(x[0] - x[1]), ps)) / float(len(ps)))
                data_rows[p[0]].append(ps)
            else:
                data_rows[p[0]].append('0')
        data_rows[p[0]].append('')

out.writerow(header_row)
out.writerows(data_rows)
out.writerow([])

f.close()
