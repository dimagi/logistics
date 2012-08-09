from datetime import timedelta
from rapidsms.conf import settings
from logistics.const import Reports

class ConsumptionSettings(object):
    
    def __init__(self, config):
        self.min_transactions = config.get("MINIMUM_TRANSACTIONS", 2)
        self.min_days = config.get("MINIMUM_DAYS", 10)
        self.max_days = config.get("MAXIMUM_DAYS", None)
        self.include_end_stockouts = config.get("INCLUDE_END_STOCKOUTS", False)
    
    @classmethod
    def default(cls):
        return ConsumptionSettings(settings.LOGISTICS_CONSUMPTION)

def daily_consumption(supply_point, product, datespan=None, 
                      consumption_settings=None):
    """
    Calculate daily consumption through the following algorithm:

    Consider each non-stockout SOH report to be the start of a period.
    We iterate through the stock transactions following it until we reach another SOH.
    If it's a stockout, we drop the period from the calculation.

    We keep track of the total receipts in each period and add them to the start quantity.
    The total quantity consumed is: (Start SOH Quantity + SUM(receipts during period) - End SOH Quantity)

    We add the quantity consumed and the length of the period to the running count,
    then at the end divide one by the other.

    This algorithm effectively deals with cases where a SOH report immediately follows a receipt.
    """
    from logistics.models import StockTransaction
    
    consumption_settings = consumption_settings or ConsumptionSettings.default()
    
    time = timedelta(0)
    quantity = 0
    
    txs = StockTransaction.objects.filter\
        (supply_point=supply_point,product=product).order_by('date')
    
    if datespan:
        txs = txs.filter(date__gte=datespan.startdate,
                         date__lte=datespan.enddate)
    if txs.count() < consumption_settings.min_transactions:
        return None
    period_receipts = 0
    start_soh = None
    
    for (i, t) in enumerate(txs):
        # Go through each StockTransaction in turn.
        if t.ending_balance == 0 and not consumption_settings.include_end_stockouts:
            # Stockout -- pass on this period
            start_soh = None
            period_receipts = 0
            continue
        if t.product_report.report_type.code == Reports.SOH:
            if start_soh:
                # End of a period.
                if t.ending_balance > (start_soh.ending_balance + period_receipts):
                    # Anomalous data point (reported higher stock than possible)
                    start_soh = None
                    period_receipts = 0
                    continue
                # Add the period stats to the running count.
                quantity += ((start_soh.ending_balance + period_receipts) - t.ending_balance)
                time += (t.date - start_soh.date)
            # Start a new period.
            start_soh = t
            period_receipts = 0
        elif t.product_report.report_type.code == Reports.REC:
            # Receipt.
            if start_soh:
                # Mid-period receipt, so we care about it.
                period_receipts += t.quantity
    days = time.days
    if days < consumption_settings.min_days:
        return None
    return round(abs(float(quantity) / float(days)),2)

