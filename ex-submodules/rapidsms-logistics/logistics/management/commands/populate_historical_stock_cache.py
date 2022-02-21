from logistics.models import SupplyPoint, StockTransaction, \
    Product, HistoricalStockCache
from datetime import datetime, timedelta
from django.core.management.base import LabelCommand

def _date_in_next_month(date):
    return datetime(date.year, date.month, 1) + timedelta(days=32)

class Command(LabelCommand):
    help = "Populates the historical stock cache."
    
    def handle(self, *args, **options):
        products = Product.objects.all()
        for sp in SupplyPoint.objects.all():
            print "generating stock for %s" % sp
            for p in products:
                transactions = StockTransaction.objects.filter(supply_point=sp,
                                                             product=p)
                if transactions.count():
                    date = transactions.order_by("date")[0].date
                    print "product %s, starting on %s" % (p, date)
                    
                    end = _date_in_next_month(datetime.utcnow())
                    while date < end:
                        cached = HistoricalStockCache.objects\
                            .get_or_create(supply_point=sp, product=p, 
                                           year=date.year, month=date.month,
                                           stock=0)[0]
                        stock = sp.historical_stock(p, date.year, date.month)
                        if cached.stock != stock:
                            cached.stock = stock
                            cached.save()
                        
                        date = _date_in_next_month(date)
