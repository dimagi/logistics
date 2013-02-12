import sys
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from dimagi.utils.couch.database import get_db
from dimagi.utils.dates import DateSpan
from rapidsms.contrib.locations.models import Location
from logistics_project.apps.ewsghana import loader
from logistics.models import SupplyPoint
from logistics.reports import ReportingBreakdown

class Command(BaseCommand):
    help = "Save M&E indicators to files in /tmp"
    frhp_regions = ['central', 'gar', 'western']
    deliver_regions = ['ashanti', 'brong_ahafo', 'upper_east', 'upper_west', 
                       'volta', 'eastern', 'northern']
    deliver_commodities = ['ns', 'nv', 'fr', 'cb', 'zs', 'oq', 'ef']

    def handle(self, *args, **options):
        #self.stat_weblogins()
        #self.stats_timeliness(self.deliver_regions, 'reporting_deliver.csv')
        #self.stats_timeliness(self.frhp_regions, 'reporting_frhp.csv')
        #self.stats_stocks(self.deliver_regions, 'stocks_deliver.csv', self.deliver_commodities)
        #self.stats_stocks(self.frhp_regions, 'stats_frhp.csv')
        self.stats_stock_group(self.deliver_regions, 'adequate_stock_deliver.csv', self.deliver_commodities)
        
    def stat_weblogins(self):
        from auditcare.models import couchmodels
        from logistics.models import LogisticsProfile
        auditEvents = couchmodels.AccessAudit.view("auditcare/by_date_access_events", descending=True, include_docs=True).all()
        realEvents = [(a.event_date, 
                       a.user, 
                       a.doc_type, 
                       a.access_type) for a in auditEvents]
        with open('/tmp/ews_weblogin.csv', 'w') as f:
            f.write(", ".join(["login date", "username", "access type", 
                              "designation", "location", 
                              "facility"]))
            f.write('\n')
            for event in realEvents:
                date, username, doc_type, access_type = event
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    designation = location = supply_point = 'None'
                else:
                    try:
                        profile = user.get_profile()
                    except LogisticsProfile.DoesNotExist:
                        designation = location = supply_point = 'None'
                    else:
                        designation = unicode(profile.designation)
                        location = unicode(profile.location)
                        supply_point = unicode(profile.supply_point)
                f.write(", ".join([unicode(date), username, access_type, 
                                  designation, location, 
                                  supply_point]))
                f.write('\n')
                
    def stats_timeliness(self, regions, filename):
        locations = Location.objects.none()
        for reg in regions:
            loc = Location.objects.get(code=reg)
            locations = locations | loc.get_descendants(include_self = True)
        self._print_reporting_stats(locations, filename)

    def stats_stock_group(self, region_codes, filename, commodities):
        regions = [Location.objects.get(code=region_code) for region_code in region_codes]
        with open('/tmp/%s' % filename, 'w') as f:
            f.write(", ".join(["start of period", "end of period"]))
            for commodity in commodities:
                f.write(", stockout of %s" % commodity)
            f.write('\n')
            end_date = self.get_day_of_week(datetime.now(), 3)
            for i in range(1,50):
                start_date = end_date - timedelta(days=7)
                f.write("%s, %s" % (start_date, end_date))
                print "processing date %s" % start_date
                datespan = DateSpan(start_date, end_date)
                safe_add = lambda x, y: x + y if y is not None else x
                for commodity in commodities:
                    stock_count = 0
                    for region in regions:
                        #print "processing commodity %s in region %s" % (commodity, region)
                        #stockout = safe_add(stockout, region.stockout_count(product=commodity, datespan=datespan))
                        stock_count = safe_add(stock_count, region.good_supply_count(product=commodity, datespan=datespan))
                    f.write(", %s" % stock_count)
                f.write("\n")
                end_date = start_date
            f.flush()

    def stats_stocks(self, region_codes, filename, commodities=None):
        regions = [Location.objects.get(code=region_code) for region_code in region_codes]
        with open('/tmp/%s' % filename, 'w') as f:
            f.write(", ".join(["start of period", "end of period", "total facilities", 
                               "stock out", "low stock", "adequate stock", "overstock"]))
            f.write('\n')
            end_date = self.get_day_of_week(datetime.now(), 3)
            for i in range(1,50):
                start_date = end_date - timedelta(days=7)
                print "processing date %s" % start_date
                datespan = DateSpan(start_date, end_date)
                
                stockout = low = adequate = overstock = total = 0
                safe_add = lambda x, y: x + y if y is not None else x
                if commodities is not None:
                    for commodity in commodities:
                        total = 0
                        for region in regions:
                            print "processing commodity %s in region %s" % (commodity, region)
                            stockout = safe_add(stockout, 
                                                region.stockout_count(product=commodity, datespan=datespan))
                            low = safe_add(low, 
                                                region.emergency_plus_low(product=commodity, datespan=datespan))
                            adequate = safe_add(adequate, 
                                                region.good_supply_count(product=commodity, datespan=datespan))
                            overstock = safe_add(overstock, 
                                                region.overstocked_count(product=commodity, datespan=datespan))
                            total = stockout+low+adequate+overstock+safe_add(total, 
                                    region.other_count(product=commodity, datespan=datespan))
                    f.write("%s, %s, %s, %s, %s, %s, %s\n" % (start_date, end_date, total, 
                                                          stockout, low, adequate, overstock))
                else:
                    for region in regions:
                        print "processing region %s" % region
                        stockout = safe_add(stockout, region.stockout_count(datespan=datespan))
                        low = safe_add(low, region.emergency_plus_low(datespan=datespan))
                        adequate = safe_add(adequate, region.good_supply_count(datespan=datespan))
                        overstock = safe_add(overstock, region.overstocked_count(datespan=datespan))
                        total = safe_add(total, region.other_count(datespan=datespan))+\
                                stockout+low+adequate+overstock
                    f.write("%s, %s, %s, %s, %s, %s, %s\n" % (start_date, end_date, total, 
                                                          stockout, low, adequate, overstock))
                end_date = start_date 

    def _print_reporting_stats(self, locations, filename):
        base_points = SupplyPoint.objects.filter(location__in=locations, active=True)
        if base_points.count() == 0:
            return
        with open('/tmp/%s' % filename, 'w') as f:
            f.write(", ".join(["start of period", "end of period", "total num facilities", "# reporting", "# on time", "# late"]))
            f.write('\n')
            end_date = self.get_day_of_week(datetime.now(), 3)
            for i in range(1,50):
                start_date = end_date - timedelta(days=7)
                datespan = DateSpan(start_date, end_date)
                report = ReportingBreakdown(base_points, datespan,  
                                            include_late=True, days_for_late=5)
                late = report.reported_late.count()
                on_time = report.reported_on_time.count()
                total = base_points.count()
                f.write("%s, %s, %s, %s, %s, %s\n" % (start_date, end_date, total, 
                                                      report.reported.count(), 
                                                      on_time, late))
                                                  #on_time/float(total), late/float(total)))
                end_date = start_date 
    
    def get_day_of_week(self, date, day_of_week):
        weekday_delta = day_of_week - date.weekday()
        return date + timedelta(days=weekday_delta)            

