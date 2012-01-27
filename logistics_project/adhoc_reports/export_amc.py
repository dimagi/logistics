import csv
from apps.malawi.util import hsa_supply_points_below
from logistics.models import *

f = file('out.csv', 'w')
out = csv.writer(f)

headers = ['Product', 'HSAs Stocking Product', 'Global Average AMC']
ds = Location.objects.filter(type='district')
headers.extend([d.name for d in ds])
out.writerow(headers)

for p in Product.objects.all():
    q = ProductStock.objects.filter(product=p)
    row = []
    qv = [x.monthly_consumption for x in q]
    row.extend([p.name, len(qv), sum(qv)/float(len(qv))])
    for d in Location.objects.filter(type="district"):
        ps = q.filter(supply_point__in=hsa_supply_points_below(d))
        qq = [x.monthly_consumption for x in ps]
        if len(qq):
            avg = sum(qq)/float(len(qq))
            print avg
            row.append(avg)
        else:
            row.append('-')
    out.writerow(row)

f.close()
