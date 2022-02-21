import csv
from apps.malawi.util import hsa_supply_points_below
from logistics.models import *
from calendar import month_name
from django.db.models.expressions import F
from logistics_project.utils.dates import DateSpan
from datetime import date, timedelta
from logistics.reports import ReportingBreakdown

f = file('reporting.csv', 'w')
out = csv.writer(f)

months = [(2011, x) for x in range(4,13)]
months.append((2012,1))

header_row = []
reported_row = []
on_time_row = []
late_row = []
not_reported_row = []
pct_row = []
for m in months:
    header_row.append("%s %s" % (month_name[m[1]], m[0]))
    ds = Location.objects.filter(type='district')
    header_row.extend([d.name for d in ds])
    header_row.append('')
    reported_row.append('Reported')
    on_time_row.append('On Time')
    late_row.append('Late')
    not_reported_row.append('Did Not Report')
    pct_row.append('Reporting %')
    if m[1] < 12:
        datespan = DateSpan(date(m[0], m[1], 1), date(m[0], m[1]+1, 1)-timedelta(seconds=1))
    else:
        datespan = DateSpan(date(m[0], m[1], 1), date(m[0]+1, 1, 1)-timedelta(seconds=1))

    for d in ds:
        sps = hsa_supply_points_below(d)
        rd = ReportingBreakdown(sps, datespan=datespan, include_late=True)
        reported_row.append(len(rd.reported))
        not_reported_row.append(len(rd.non_reporting))
        late_row.append(len(rd.reported_late))
        on_time_row.append(len(rd.reported_on_time))
        if len(sps):
            pct_row.append("%.2f%%" % (len(rd.reported)*100.0 / float(len(sps))))
        else:
            pct_row.append("0%")

    reported_row.append('')
    not_reported_row.append('')
    late_row.append('')
    pct_row.append('')
    on_time_row.append('')

out.writerow(header_row)
out.writerow(reported_row)
out.writerow(on_time_row)
out.writerow(late_row)
out.writerow(not_reported_row)
out.writerow(pct_row)

f.close()
