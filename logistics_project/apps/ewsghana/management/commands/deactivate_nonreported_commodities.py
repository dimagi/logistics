from django.core.management.base import BaseCommand
from logistics.util import config

class Command(BaseCommand):
    help = "Mark all product stocks as 'inactive' which don't have an associated reporter"

    def handle(self, *args, **options):
        from logistics.models import ProductStock, SupplyPoint
        count = 0
        sps = SupplyPoint.objects.\
          exclude(type__code=config.SupplyPointCodes.REGIONAL_MEDICAL_STORE).\
          select_related('productstock')
        for sp in sps:
            commodities_reported = sp.commodities_reported()
            stocks = sp.productstock_set.all()
            for stock in stocks:
                if stock.product not in commodities_reported and stock.is_active:
                    stock.is_active = False
                    stock.save()
                    count = count + 1
                    print "(%s-%s) marked inactive" % (stock.supply_point.name, stock.product.name)
        print "%s stocks marked as 'inactive'" % count