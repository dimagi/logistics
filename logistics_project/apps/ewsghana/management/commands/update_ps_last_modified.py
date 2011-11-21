import sys
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from dimagi.utils.couch.database import get_db
from logistics_project.apps.ewsghana import loader

class Command(BaseCommand):
    help = "Update Product Stock's 'last modified' field on the basis of last reports received"

    def handle(self, *args, **options):
        from logistics.models import ProductReport, ProductStock
        stocks = ProductStock.objects.all()
        count = 0
        for stock in stocks:
            prs = ProductReport.objects.filter(product=stock.product, 
                                               supply_point=stock.supply_point).\
                                               order_by('-report_date','-pk')
            if prs.exists():
                if stock.last_modified != prs[0].report_date:
                    stock.last_modified = prs[0].report_date
                    stock.save()
                    count = count + 1
        print "%s modification dates updated" % (count)
