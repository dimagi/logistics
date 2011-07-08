import gviz_api
from logistics.models import ProductReportType, Product
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
        
