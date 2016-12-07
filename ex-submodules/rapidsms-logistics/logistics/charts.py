from datetime import datetime
from dimagi.utils.dates import DateSpan, get_day_of_month
from dateutil.relativedelta import relativedelta
from django.core.cache import cache
import gviz_api
from logistics.models import ProductReportType, Product, ProductStock
from logistics.const import Reports


def stocklevel_plot(transactions):
    products = transactions.values_list("product__sms_code", flat=True).distinct()
    cols = {"date": ("datetime", "Date")}
    for p in products:
        product = Product.objects.get(sms_code=p)
        if product.average_monthly_consumption:
            cols[product.name] = ('number', p)#, {'type': 'string', 'label': "title_"+s.sms_code}]
    table = gviz_api.DataTable(cols)

    data_rows = {}
    for t in transactions:
        if not t.product.average_monthly_consumption: continue
        if not t.date in data_rows: data_rows[t.date] = {}
        data_rows[t.date][t.product.name] = float(t.ending_balance) / float(t.product.average_monthly_consumption)
        
    rows = []
    for d in data_rows.keys():
        q = {"date":d}
        q.update(data_rows[d])
        rows += [q]
    if not rows:
        return None
    table.LoadData(rows)
    chart_data = table.ToJSCode("chart_data", columns_order=["date"] + [x for x in cols.keys() if x != "date"],
                                order_by="date")
    return chart_data
        
def amc_plot(sps, datespan, products=None):
    cols = {"date": ("datetime", "Date")}
    products = products or Product.objects.all().order_by('sms_code')
    for p in products:
        if p.average_monthly_consumption:
            cols[p.sms_code] = ('number', p.sms_code)#, {'type': 'string', 'label': "title_"+s.sms_code}]
    table = gviz_api.DataTable(cols)

    data_rows = {}
    for year, month in datespan.months_iterator():
        dm = DateSpan(startdate=datetime(year,month,1)-relativedelta(months=2), enddate=get_day_of_month(year, month, -1))
        dt = datetime(year, month, 1)
        if not dt in data_rows: data_rows[dt] = {}
        for pr in products:
            cache_key = "log-amc-%s-%s-%s" % (pr.sms_code, year, month)
            cached_amc = cache.get(cache_key)
            if cached_amc is not None:
                data_rows[dt][pr.sms_code] = cached_amc
            else:
                ps = ProductStock.objects.filter(supply_point__in=sps, product=pr, is_active=True)
                total = 0.0
                count = 0.0
                for p in ps:
                    try:
                        total += p.get_daily_consumption(datespan=dm) * 30.0
                        count += 1
                    except:
                        continue
                amc_avg = total / count if count else 0
                cache.set(cache_key, amc_avg, (30 * 24 * 60 * 60) - 1)
                data_rows[dt][pr.sms_code] = amc_avg

    rows = []
    for d in data_rows.keys():
        q = {"date":d}
        q.update(data_rows[d])
        rows += [q]
    if not rows:
        return None
    table.LoadData(rows)

    chart_data = table.ToJSCode("chart_data", columns_order=["date"] + [x for x in cols.keys() if x != "date"],
        order_by="date")
    return chart_data, data_rows
