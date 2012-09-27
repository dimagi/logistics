import sys
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from dimagi.utils.couch.database import get_db
from logistics.models import *
from logistics.util import config
from logistics_project.apps.ewsghana import loader

class Command(BaseCommand):
    help = "Set ProductStock.use_auto_consumption to be True, and update all auto_monthly_consumptions"

    def handle(self, *args, **options):
        self.list_stockouts_by_commodity()
        self.number_of_missing_consumption_values()
        self.stocks_unreported_for_x_months()
        self.default_consumptions_per_facility_types()
        self.unregistered_commodities()
        
    def list_stockouts_by_commodity(self):
        products = Product.objects.all().order_by('name')
        stockouts = {}
        for prod in products:
            stockouts[prod.name] = ProductStock.objects.filter(product=prod, quantity=0, is_active=True).count()
        product_names = [prod.name for prod in products]
        sorted_products = sorted(product_names, key=stockouts.__getitem__)
        total_stockouts = 0
        for sorted_product in sorted_products:
            print "%s, %s" % (sorted_product, stockouts[sorted_product])
            total_stockouts += stockouts[sorted_product]
        print "Total stockouts: %s" % (total_stockouts)

    def number_of_missing_consumption_values(self):
        facs = SupplyPoint.objects.all().order_by('name')
        stock_count = 0
        fac_count = 0
        for fac in facs:
            stocks = fac.productstock_set.filter(is_active=True).all()
            no_consumption = False
            for stock in stocks:
                if stock.monthly_consumption == None:
                    no_consumption = True
                    stock_count += 1
                    print "%s, %s has no consumption defined (%s)" % (stock.supply_point, stock.product, stock.pk)
            if no_consumption == True:
                fac_count += 1
        print "%s productstocks in %s facilities have no consumption defined" % (stock_count, fac_count)
        
    def stocks_unreported_for_x_months(self):
        facs = SupplyPoint.objects.all().order_by('name')
        stock_count = 0
        fac_count = 0
        three_months_ago = datetime.utcnow() - timedelta(days=90)
        print "Facility, Product, Someone Assigned, Last Reported, District, Region"
        assigned_unreporting = 0
        unassigned_unreporting = 0
        for fac in facs:
            commodities_reported = fac.commodities_reported()
            stocks = fac.productstock_set.filter(last_modified__lt=three_months_ago).filter(is_active=True)
            for stock in stocks:
                someone_assigned = True
                if stock.product not in commodities_reported:
                    someone_assigned = False
                    assigned_unreporting += 1
                region = ''
                if fac.location.parent.parent is not None:
                    region = fac.location.parent.parent
                    unassigned_unreporting += 1
                print "%s, %s, %s, %s, %s, %s" % (stock.supply_point, stock.product, someone_assigned, 
                                      stock.last_modified, fac.location.parent, region)
                #print "%s, %s has not been reported in the last 3 months" % (stock.supply_point, stock.product)
        print "%s assigned, %s unassigned" % (assigned_unreporting, unassigned_unreporting)

    def default_consumptions_per_facility_types(self):
        products = Product.objects.all().order_by('name')
        types = SupplyPointType.objects.all().order_by('name')
        print "Average Consumption, Product, Facility Type, number of facilities used to calculate this average" 
        for type in types:
            for prod in products:
                ps = ProductStock.objects.filter(product=prod, supply_point__type=type, is_active=True)
                fac_count = 0
                total_consumption = 0
                for p in ps:
                    if p.monthly_consumption is not None:
                        total_consumption += p.monthly_consumption 
                        fac_count += 1
                if fac_count != 0:
                    cons = float(total_consumption)/ float(fac_count)
                    #print "consumption: %s, product: %s, type: %s based on %s facilities" % (cons, prod.name, type.name, fac_count)
                    print "%s, %s, %s, %s" % (cons, prod.name, type.name, fac_count)
    
    def unregistered_commodities(self):
        count = 0
        sps = SupplyPoint.objects.\
          exclude(type__code=config.SupplyPointCodes.REGIONAL_MEDICAL_STORE).\
          select_related('productstock')
        print "Facility, Facility Type, Product, Number of SMS Reports, District, Region" 
        for sp in sps:
            commodities_reported = sp.commodities_reported()
            stocks = sp.productstock_set.filter(is_active=True)
            for stock in stocks:
                if stock.product not in commodities_reported:
                    report_count = ProductReport.objects.filter(product=stock.product, supply_point=stock.supply_point).count()
                    region = ''
                    if stock.supply_point.location.parent.parent is not None:
                        region = stock.supply_point.location.parent.parent
                    print "%s, %s, %s, %s, %s, %s" % (stock.supply_point.name, 
                                              stock.supply_point.type.name, 
                                              stock.product.name, 
                                              report_count, 
                                              stock.supply_point.location.parent,
                                              stock.supply_point.location.parent.parent)
                    #print "Facility %s: Stock %s has no active reporters, and has only been reported %s times" % (stock.supply_point.name, 
                    #                                                                                                stock.product.name, 
                    #                                                                                                report_count)
                    count = count + 1
        print "%s stocks are not assigned to SMS reporters properly" % count        
        