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
        self.report_userprod_facilityprod()
        
    def report_userprod_facilityprod(self):
        sps = SupplyPoint.objects.\
          exclude(type__code=config.SupplyPointCodes.REGIONAL_MEDICAL_STORE).\
          select_related('productstock').order_by('name')
        #print "person, phone number, facility, district, region, OLD commodities, NEW commodities, DIFFERENCES" 
        add_product_count = 0
        remove_product_count = 0
        facility_count = 0
        reporter_count = 0
        for sp in sps:
            will_modify = False
            will_report = Product.objects.filter(is_active=True, reported_by__supply_point=sp).distinct()
            for reporter in sp.reporters().order_by('name'):
                used_to_report = reporter.commodities.all()
                used_to_report_codes = [c.sms_code for c in used_to_report]
                will_report_codes = [c.sms_code for c in will_report]
                differences = []
                for code in will_report_codes:
                    if code not in used_to_report_codes:
                        differences.append("+%s" % code)
                        add_product_count = add_product_count + 1
                for code in used_to_report_codes:
                    if code not in will_report_codes:
                        differences.append("-%s" % code)
                        remove_product_count = remove_product_count + 1
                if differences:
                    reporter_count = reporter_count + 1
                    will_modify = True
            if will_modify:
                facility_count = facility_count + 1
                print "%s, %s, %s, %s, %s, %s, %s, %s" % (reporter.name, 
                                          reporter.default_connection.identity if reporter.default_connection else None, 
                                          reporter.supply_point, 
                                          reporter.supply_point.location.parent, 
                                          reporter.supply_point.location.parent.parent, 
                                          " ".join(used_to_report_codes),
                                          " ".join(will_report_codes),
                                          " ".join(differences))
        
#        print "%s added, %s removed, affecting %s reporters in %s facilities" % (add_product_count, 
#                                                                                remove_product_count, 
#                                                                                facility_count, 
#                                                                                reporter_count)
        
