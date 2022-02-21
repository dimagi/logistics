from datetime import datetime, timedelta
from rapidsms.conf import settings
from logistics.const import Reports
from dimagi.utils.dates import delta_secs

class ConsumptionSettings(object):
    
    def __init__(self, config):
        self.min_transactions = config.get("MINIMUM_TRANSACTIONS", 2)
        self.min_days = config.get("MINIMUM_DAYS", 10)
        self.lookback_days = config.get("LOOKBACK_DAYS", None)
        self.include_end_stockouts = config.get("INCLUDE_END_STOCKOUTS", False)
    
    @property
    def cutoff_date(self):
        """
        The cutoff date for calculating consumption. Always calculated 
        relative to the current date.
        """
        return datetime.min if not self.lookback_days else \
            datetime.utcnow() - timedelta(days=self.lookback_days )
        
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
    
    total_time = timedelta(0)
    total_consumption = 0
    
    txs = StockTransaction.objects.filter\
        (supply_point=supply_point,product=product).order_by('-date')
    
    if datespan:
        txs = txs.filter(date__gte=datespan.startdate,
                         date__lte=datespan.enddate)
    if txs.count() < consumption_settings.min_transactions:
        return None
    period_receipts = 0
    end_transaction = None
    for t in txs:
        # Go through each StockTransaction in turn (backwards!).
        if t.ending_balance == 0 and not consumption_settings.include_end_stockouts:
            # Previous period ended in stockout -- pass on this period
            end_transaction = None
            period_receipts = 0
            continue
        if t.product_report.report_type.code == Reports.SOH:
            if end_transaction:
                # End of a period.
                if t.ending_balance + period_receipts >= end_transaction.ending_balance:
                    # if this check fails it's an anomalous data point 
                    # (finished with higher stock than possible)
                    
                    # Add the period stats to the running count.
                    # But first scale them if they fall within the cutoff window
                    period_time = (end_transaction.date - t.date)
                    period_consumption = t.ending_balance + period_receipts - end_transaction.ending_balance
                    
                    scaling_factor = 1 if consumption_settings.cutoff_date < t.date \
                        else max(0, delta_secs(end_transaction.date - consumption_settings.cutoff_date) \
                                    / delta_secs(period_time))
                    
                    total_time += timedelta(seconds=scaling_factor * delta_secs(period_time))
                    total_consumption += scaling_factor * period_consumption
                    
            if t.date < consumption_settings.cutoff_date:
                break
            else:
                # Start a new period.
                end_transaction = t
                period_receipts = 0
            
        elif t.product_report.report_type.code == Reports.REC:
            # Receipt.
            if end_transaction:
                # Mid-period receipt, so we care about it.
                period_receipts += t.quantity
    days = total_time.days
    if days < consumption_settings.min_days:
        return None
    return round(abs((float(total_consumption) / delta_secs(total_time)) * 60*60*24),2)

