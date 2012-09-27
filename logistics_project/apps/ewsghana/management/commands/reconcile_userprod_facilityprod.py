import sys
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from dimagi.utils.couch.database import get_db
from logistics.models import *
from logistics.util import config
from logistics_project.apps.ewsghana import loader

class Command(BaseCommand):
    help = "Switch from STOCK_BY = user to STOCKY_BY = facility"

    def handle(self, *args, **options):
        self.reconcile_userprod_facilityprod()
        
    def reconcile_userprod_facilityprod(self):
        sps = SupplyPoint.objects.\
          exclude(type__code=config.SupplyPointCodes.REGIONAL_MEDICAL_STORE).\
          select_related('productstock').order_by('name')
        print "ID, facility, district, region, OLD commodities, NEW commodities, DIFFERENCES" 
        
        
        shouldbeinactive_stocks = ProductStock.objects.filter(product__is_active=False, is_active=True)
        if shouldbeinactive_stocks:
            print "Deactivating %s product stocks for inactive products" % shouldbeinactive_stocks.count()
            for sbi_stock in shouldbeinactive_stocks:
                sbi_stock.is_active = False
                sbi_stock.save()
        for sp in sps:
            active_stock = ProductStock.objects.filter(supply_point=sp, is_active=True)
            active_stock_codes = [stocky.product.sms_code for stocky in active_stock]
            total_reported = Product.objects.filter(is_active=True, reported_by__supply_point=sp).distinct()
            total_reported_code = [prodx.sms_code for prodx in total_reported]
            differences = []
            for stock in active_stock:
                # remove unnecessary stock
                if stock.product.sms_code not in total_reported_code:
                    stock.is_active = False
                    stock.save()
                    differences.append("-%s" % stock.product.sms_code)
                    active_stock_codes.append(stock.product.sms_code)
            for product in total_reported:
                if product.code not in active_stock_codes:
                    try:
                        ps = ProductStock.objects.get(supply_point=sp, product=product)
                    except ProductStock.DoesNotExist:
                        ps = ProductStock(supply_point=sp, product=product)
                    else:
                        assert (ps.is_active==False)
                    ps.is_active = True
                    ps.save()
                    differences.append("+%s" % product.code)
            print "%s, %s, %s, %s, %s, %s, %s" % (sp.pk, sp, 
                                      sp.location.parent, 
                                      sp.location.parent.parent, 
                                      " ".join([ps.product.sms_code for ps in active_stock]),
                                      " ".join([p.sms_code for p in total_reported]),
                                      " ".join(differences))
    