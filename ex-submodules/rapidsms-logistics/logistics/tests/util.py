from datetime import timedelta
from logistics import loader as logi_loader
from logistics.const import Reports
from logistics.models import StockTransaction, ProductStock

def load_test_data():
    logi_loader.init_reports()
    logi_loader.init_supply_point_types()
    logi_loader.init_test_location_and_supplypoints()
    logi_loader.init_test_product_and_stock()
    
def fake_report(supply_point, product, amount, days_ago, report_type):
    """
    Fake a stock report, sometime in the past, generating the appropriate 
    models.
    """
    if report_type == Reports.SOH:
        report = supply_point.report_stock(product, amount)
    else:
        report = supply_point.report_receipt(product, amount)
    
    txs = StockTransaction.objects.filter(product_report=report).order_by('-pk')
    try:
        trans = txs[0]
    except IndexError:
        # no big deal; it wasn't a transaction-generating report
        pass
    else:
        trans.date = trans.date - timedelta(days=days_ago)
        trans.save()
    # NB: it is important that we draw this from the database since the automatic
    # stock calculation works by updating the productstock.auto_monthly_consumption field
    return ProductStock.objects.get(supply_point=supply_point, product=product)
