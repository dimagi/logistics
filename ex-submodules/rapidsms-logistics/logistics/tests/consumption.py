from __future__ import unicode_literals
from datetime import timedelta
from rapidsms.conf import settings
from django.core.cache import cache
from rapidsms.tests.scripted import TestScript
from logistics.models import Location, SupplyPointType, SupplyPoint, \
    Product, ProductType, ProductStock, StockTransaction, ProductReport, \
    ProductReportType
from logistics.models import SupplyPoint as Facility
from logistics.tests.util import load_test_data, fake_report
from logistics.const import Reports

class TestConsumption (TestScript):
    def setUp(self):
        TestScript.setUp(self)

        load_test_data()
        
        settings.LOGISTICS_CONSUMPTION["MINIMUM_DAYS"] = 10
        settings.LOGISTICS_CONSUMPTION["MINIMUM_TRANSACTIONS"] = 2
        settings.LOGISTICS_CONSUMPTION["LOOKBACK_DAYS"] = None
        settings.LOGISTICS_CONSUMPTION["INCLUDE_END_STOCKOUTS"] = False
        
        self.pr = Product.objects.all()[0]
        self.sp = Facility.objects.all()[0]
        self.ps = ProductStock.objects.get(supply_point=self.sp, product=self.pr)
        self.ps.use_auto_consumption = True
        self.ps.save()
       
    def testBasicConsumption(self):
        # now enable auto_monthly_consumption
        self.ps = self._report(30, 30, Reports.SOH) 
        self.ps = self._report(20, 20, Reports.SOH) 
        self.ps = self._report(10, 10, Reports.SOH) 
        self.assertEqual(1, round(self.ps.daily_consumption))
        self.ps.use_auto_consumption = False
        self.assertEqual(5, round(self.ps.monthly_consumption))
        self.ps.use_auto_consumption = True
        self.assertEqual(1, round(self.ps.daily_consumption))
        self.assertEqual(30, round(self.ps.monthly_consumption))
    
    def testConsumption(self):
        self.sp.report_stock(self.pr, 200) 

        # Not enough data.
        self.assertEqual(None, self.ps.daily_consumption)
        self.assertEqual(self.ps.product.average_monthly_consumption, self.ps.monthly_consumption) #fallback

        self.ps.monthly_consumption = 999

        st = StockTransaction.objects.get(supply_point=self.sp,product=self.pr)
        st.date = st.date - timedelta(days=5)
        st.save()
        self.sp.report_stock(self.pr, 150)
        
        # 5 days still aren't enough to compute.
        self.ps = ProductStock.objects.get(supply_point=self.sp, product=self.pr)
        self.assertEqual(None, self.ps.daily_consumption)
        self.assertEqual(self.ps.monthly_consumption, self.ps.monthly_consumption)

        sta = StockTransaction.objects.filter(supply_point=self.sp,product=self.pr)
        for st in sta:
            st.date = st.date - timedelta(days=5)
            st.save()
        self.sp.report_stock(self.pr, 100)

        # 10 days is enough.
        self.ps = ProductStock.objects.get(supply_point=self.sp, product=self.pr)
        # 200 in stock 10 days ago, 150 in stock 5 days ago, 100 now
        self.assertEqual(10, round(self.ps.daily_consumption)) 
        self.assertEqual(300, round(self.ps.monthly_consumption))

        sta = StockTransaction.objects.filter(supply_point=self.sp,product=self.pr)
        for st in sta:
            st.date = st.date - timedelta(days=10)
            st.save()
        # 200 in stock 20 days ago, 150 in stock 15 days ago, 100 10 days ago, 50 now
        self.sp.report_stock(self.pr, 50) 

        # Another data point.
        self.ps = ProductStock.objects.get(supply_point=self.sp, product=self.pr)
        self.assertEqual(7.5, round(self.ps.daily_consumption, 1))
        # Make sure the rounding is correct
        self.assertEqual(225, round(self.ps.monthly_consumption))

        sta = StockTransaction.objects.filter(supply_point=self.sp,product=self.pr)
        for st in sta:
            st.date = st.date - timedelta(days=10)
            st.save()
        self.sp.report_stock(self.pr, 100)

        # Reporting higher stock shouldn't change the daily consumption
        # since we have no way of knowing how much was received vs dispensed.
        self.ps = ProductStock.objects.get(supply_point=self.sp, product=self.pr)
        self.assertEqual(7.5, round(self.ps.daily_consumption, 1))

        npr = ProductReport(product=self.pr, report_type=ProductReportType.objects.get(code=Reports.REC),
                            quantity=10000, message=None, supply_point=self.sp)
        npr.save()
        
        # Make sure receipts after a soh report don't change the daily consumption
        # since we don't know what the new balance is. Only change consumption 
        # when we get the soh report after the receipt.
        self.ps = ProductStock.objects.get(supply_point=self.sp, product=self.pr)
        self.assertEqual(7.5, round(self.ps.daily_consumption, 1))

    def testConsumptionWithMultipleReports(self):
        self.ps = ProductStock.objects.get(supply_point=self.sp,
                                           product=self.pr)
        self.ps.use_auto_consumption = True
        self.ps.save()
                    
        self.ps = self._report(40, 60, Reports.SOH) # 60 days ago we had 40 in stock. 
        self.assertEqual(None, self.ps.daily_consumption)

        self.ps = self._report(30, 50, Reports.REC) # 50 days ago, we received 30
        self.assertEqual(None, self.ps.daily_consumption) # consumption unchanged

        self.ps = self._report(20, 50, Reports.SOH) # 50 days ago, we had 20 in stock (so we've consumed 50)
        self.assertEqual(5, self.ps.daily_consumption) # 50/10 days

        self.ps = self._report(10, 40, Reports.SOH) # 40 days ago we had 10 in stock (so we've consume 60 over 20 days)
        self.assertEqual(3, self.ps.daily_consumption)

    def testFloatingPointAccuracy(self):
        self.ps = self._report(10, 51, Reports.REC)
        self.assertEqual(None, self.ps.daily_consumption) # consumption unchanged

        self.ps = self._report(50, 50, Reports.SOH) 
        self.assertEqual(None, self.ps.daily_consumption)

#        self.ps = self._report(10, 41, Reports.REC)
        self.assertEqual(None, self.ps.daily_consumption) # consumption unchanged

        self.ps = self._report(30, 40, Reports.SOH)
        self.assertEqual(2, round(self.ps.daily_consumption))

        self.ps = self._report(10, 30, Reports.SOH)

        self.assertEqual(2, round(self.ps.daily_consumption)) # 20/10 days
        self.assertEqual(60, round(self.ps.monthly_consumption))

        self.ps = self._report(20, 25, Reports.REC)
        self.assertEqual(2, round(self.ps.daily_consumption)) # consumption unchanged
        self.assertEqual(60, round(self.ps.monthly_consumption))

        self.ps = self._report(0, 0, Reports.SOH)
        self.assertEqual(2, round(self.ps.daily_consumption)) # ending with a stockout shouldn't change anything
        self.assertEqual(60, round(self.ps.monthly_consumption))

    def testStockoutPeriodsNotIncluded(self):

        self.ps = self._report(50, 100, Reports.SOH)
        self.assertEqual(None, self.ps.daily_consumption)

        self.ps = self._report(40, 90, Reports.SOH)
        self.assertEqual(1.0, self.ps.daily_consumption)

        self.ps = self._report(30, 80, Reports.SOH)
        self.assertEqual(1.0, self.ps.daily_consumption)

        self.ps = self._report(0, 70, Reports.SOH) # now introduce a stockout period
        self.assertEqual(1.0, self.ps.daily_consumption)

        self.ps = self._report(60, 60, Reports.REC)
        self.assertEqual(1.0, self.ps.daily_consumption)

        self.ps = self._report(50, 50, Reports.SOH)
        self.assertEqual(1.0, self.ps.daily_consumption)

        self.ps = self._report(40, 40, Reports.SOH)
        self.assertEqual(1.0, self.ps.daily_consumption)

    def testStockoutPeriodsManuallyIncluded(self):
        
        self.ps = self._report(60, 100, Reports.SOH)
        self.assertEqual(None, self.ps.daily_consumption)
        
        self.ps = self._report(50, 90, Reports.SOH)
        self.assertEqual(1.0, self.ps.daily_consumption)
        
        self.ps = self._report(0, 80, Reports.SOH)
        self.assertEqual(1.0, self.ps.daily_consumption)
        
        settings.LOGISTICS_CONSUMPTION["INCLUDE_END_STOCKOUTS"] = True
        self.assertEqual(3.0, self.ps.daily_consumption)
        
        # this creates an anomalous period, which is ignored
        self.ps = self._report(60, 70, Reports.SOH)
        self.ps = self._report(30, 60, Reports.SOH)
        # total consumption is 90 in 30 days
        self.assertEqual(3.0, self.ps.daily_consumption)
        
        settings.LOGISTICS_CONSUMPTION["INCLUDE_END_STOCKOUTS"] = False
        # but if we're ignoring the end stockout it's 40 in 20 days
        self.assertEqual(2.0, self.ps.daily_consumption)
    
    def testLookbackWindow(self):
        settings.LOGISTICS_CONSUMPTION["MINIMUM_DAYS"] = 5
        settings.LOGISTICS_CONSUMPTION["MINIMUM_TRANSACTIONS"] = 1
        
        self.ps = self._report(130, 60, Reports.SOH)
        self.ps = self._report(70, 40, Reports.SOH)
        self.ps = self._report(30, 20, Reports.SOH)
        self.ps = self._report(10, 00, Reports.SOH)
        
        # for all time -- 120 / 60 days = 2
        self.assertEqual(2.0, self.ps.daily_consumption)
        
        settings.LOGISTICS_CONSUMPTION["LOOKBACK_DAYS"] = 61
        self.assertEqual(2.0, self.ps.daily_consumption)
        
        # for up to 20 days -- 1 per day
        settings.LOGISTICS_CONSUMPTION["LOOKBACK_DAYS"] = 10
        self.assertEqual(1.0, self.ps.daily_consumption)
        settings.LOGISTICS_CONSUMPTION["LOOKBACK_DAYS"] = 20
        self.assertEqual(1.0, self.ps.daily_consumption)
        
        # for 30 days 40 / 30 = 1.33
        settings.LOGISTICS_CONSUMPTION["LOOKBACK_DAYS"] = 30
        self.assertEqual(1.33, self.ps.daily_consumption)
        
        # for 40 days 60 / 40 = 1.5
        settings.LOGISTICS_CONSUMPTION["LOOKBACK_DAYS"] = 40
        self.assertEqual(1.5, self.ps.daily_consumption)
        
        # for 50 days 90 / 50 = 1.8
        settings.LOGISTICS_CONSUMPTION["LOOKBACK_DAYS"] = 50
        self.assertEqual(1.8, self.ps.daily_consumption)
        
    
    def testAutoVsManualConsumption(self):
        # test all combinations of use_auto_consumption, 
        # manual_consumption, and auto_consumption
        self.ps.unset_auto_consumption()
        self.assertEqual(5, self.ps.monthly_consumption)
        self.ps.set_auto_consumption()
        self.assertEqual(5, self.ps.monthly_consumption)
        self.ps.manual_monthly_consumption = 8
        self.ps.save()
        # auto consumption falls back to manual when auto is none
        self.assertEqual(8, self.ps.monthly_consumption)
        self.ps.unset_auto_consumption()
        self.assertEqual(8, self.ps.monthly_consumption)
        
        # now enable auto_monthly_consumption
        self.ps = self._report(30, 30, Reports.SOH) 
        self.ps = self._report(20, 20, Reports.SOH) 
        self.ps = self._report(10, 10, Reports.SOH) 
        self.ps.manual_monthly_consumption = None
        self.ps.save()
        self.assertEqual(5, self.ps.monthly_consumption)
        self.ps.set_auto_consumption()
        self.assertEqual(30, self.ps.monthly_consumption)
        self.ps.manual_monthly_consumption = 8
        self.ps.save()
        self.assertEqual(30, self.ps.monthly_consumption)
        self.ps.unset_auto_consumption()
        self.assertEqual(8, self.ps.monthly_consumption)

    def testFloatingPointAccuracy2(self):
        self.ps = self._report(50, 50, Reports.SOH) 
        self.ps = self._report(49, 49, Reports.SOH) 
        self.ps = self._report(48, 48, Reports.SOH) 
        self.ps = self._report(40, 40, Reports.SOH) 
        self.assertEqual(1.0, round(self.ps.daily_consumption)) 
        self.ps = self._report(38, 39, Reports.SOH) 
        self.ps = self._report(36, 38, Reports.SOH) 
        self.assertEqual(1.17, round(self.ps.daily_consumption,2)) 
        
    def testConsumptionWithMultipleReports2(self):
        self.ps = ProductStock.objects.get(supply_point=self.sp, 
                                           product=self.pr)
        self.ps.use_auto_consumption = True
        self.ps.save()
        self.ps = self._report(80, 80, Reports.SOH)
        self.ps = self._report(70, 70, Reports.SOH)
        self.ps = self._report(65, 65, Reports.SOH)
        self.ps = self._report(60, 60, Reports.SOH)
        self.assertEqual(1, round(self.ps.daily_consumption))
        self.ps = self._report(20, 55, Reports.REC) # 50 days ago, we received 30
        self.assertEqual(1, self.ps.daily_consumption) # consumption unchanged
        self.ps = self._report(40, 50, Reports.SOH) # 50 days ago, we had 20 in stock (so we've consumed 50)
        self.assertEqual(2, self.ps.daily_consumption) # 50/10 days

    def testIgnorePeriodsOfStockout(self):
        self.ps = ProductStock.objects.get(supply_point=self.sp, 
                                           product=self.pr)
        self.ps.use_auto_consumption = True
        self.ps.save()
                    
        self.ps = self._report(100, 100, Reports.SOH) 
        self.ps = self._report(90, 90, Reports.SOH) 
        self.ps = self._report(80, 80, Reports.SOH) 
        self.assertEqual(1, self.ps.daily_consumption) 
        self.ps = self._report(0, 70, Reports.SOH) 
        self.ps = self._report(0, 60, Reports.SOH) 
        self.assertEqual(1, self.ps.daily_consumption) # consumption unchanged after stockouts
        self.ps = self._report(70, 50, Reports.SOH) 
        self.ps = self._report(20, 40, Reports.SOH) 
        self.assertEqual(2, round(self.ps.daily_consumption)) # consumption changed

    def testConsumptionCalculationIntervals(self):
        self.ps = ProductStock.objects.get(supply_point=self.sp, 
                                           product=self.pr)
        self.ps.use_auto_consumption = True
        self.ps.save()
                    
        self.ps = self._report(100, 100, Reports.SOH)
        self.ps = self._report(5, 91, Reports.REC)
        self.ps = self._report(95, 90, Reports.SOH)
        self.ps = self._report(5, 81, Reports.REC)
        self.assertEqual(1, self.ps.daily_consumption)
        self.ps = self._report(90, 80, Reports.SOH)
        self.assertEqual(1, self.ps.daily_consumption)
        self.ps = self._report(5, 71, Reports.REC)
        self.ps = self._report(85, 70, Reports.SOH)
        self.assertEqual(1, self.ps.daily_consumption)
        self.ps = self._report(5, 61, Reports.REC)
        self.ps = self._report(80, 60, Reports.SOH)
        self.assertEqual(1, self.ps.daily_consumption)
    
    def testMoreComplicatedStockoutExample(self):
        self.ps = ProductStock.objects.get(supply_point=self.sp, 
                                           product=self.pr)
        self.ps.use_auto_consumption = True
        self.ps.save()
                    
        self.ps = self._report(10, 100, Reports.SOH) # 100 days ago we had 10 in stock. 
        self.assertEqual(None, self.ps.daily_consumption) # not enough data
        self.ps = self._report(5, 95, Reports.REC) 
        self.assertEqual(None, self.ps.daily_consumption) # not enough data
        self.ps = self._report(10, 95, Reports.REC) 
        self.assertEqual(None, self.ps.daily_consumption) # not enough data
        self.ps = self._report(5, 90, Reports.REC) 
        self.assertEqual(None, self.ps.daily_consumption) # not enough data


        # 90 days ago, we have 10 in stock 
        self.ps = self._report(10, 90, Reports.SOH) 
        self.assertEqual(2, self.ps.daily_consumption) # 10 stock/10 days
        
        # 80 days ago we had 0 in stock
        self.ps = self._report(0, 80, Reports.SOH) 
        self.assertEqual(2, self.ps.daily_consumption)
        # no matter how much we receive, as long as soh remains 0, nothing changes
        self.ps = self._report(50, 80, Reports.REC) 
        self.assertEqual(2, self.ps.daily_consumption)
        self.ps = self._report(100, 70, Reports.REC) 
        self.assertEqual(2, self.ps.daily_consumption)
        self.ps = self._report(30000, 60, Reports.REC) 
        self.assertEqual(2, self.ps.daily_consumption)
        self.ps = self._report(0, 50, Reports.SOH) 
        self.assertEqual(2, self.ps.daily_consumption)
        
        # only once the stockout is resolved do consumption update again
        self.ps = self._report(1, 50, Reports.SOH) 
        self.assertEqual(2, self.ps.daily_consumption)
        self.ps = self._report(180, 40, Reports.REC)
        self.assertEqual(2, self.ps.daily_consumption)
        self.ps = self._report(1, 40, Reports.SOH) 
        self.assertEqual(10, round(self.ps.daily_consumption, 0))
                
    def testNonReporting(self):
        """ For now, we don't do anything special about non-reporting"""
        self.ps = ProductStock.objects.get(supply_point=self.sp, 
                                           product=self.pr)
        self.ps.use_auto_consumption = True
        self.ps.save()
                    
        self.ps = self._report(100, 100, Reports.SOH) # 100 days ago we had 10 in stock. 
        self.assertEqual(None, self.ps.daily_consumption) # not enough data
        self.ps = self._report(10, 90, Reports.REC) # 90 days ago, we received 10
        self.assertEqual(None, self.ps.daily_consumption) # not enough data
        # 90 days ago, we have 10 in stock 
        self.ps = self._report(100, 90, Reports.SOH) 
        self.assertEqual(1, self.ps.daily_consumption) # 10 stock/10 days
        
        # even though we received no reports between day 90 and day 50
        # the consumption gets updated all the same
        self.ps = self._report(490, 50, Reports.REC) 
        self.ps = self._report(100, 50, Reports.SOH)
        self.assertEqual(10, self.ps.daily_consumption)
    
    def testAutoConsumptionSettings(self):
        settings.LOGISTICS_CONSUMPTION["MINIMUM_DAYS"] = 25
        settings.LOGISTICS_CONSUMPTION["MINIMUM_TRANSACTIONS"] = 2
        self.ps = self._report(30, 30, Reports.SOH)
        self.ps = self._report(20, 20, Reports.SOH)
        self.ps = self._report(10, 10, Reports.SOH)
        self.assertEqual(None, self.ps.daily_consumption)
        self.ps = self._report(5, 5, Reports.SOH)
        self.assertEqual(1, self.ps.daily_consumption)

    def _report(self, amount, days_ago, report_type):
        self.ps = fake_report(self.sp, self.pr, amount, days_ago, report_type)[1]
        return self.ps
    
    def tearDown(self):
        Location.objects.all().delete()
        SupplyPoint.objects.all().delete()
        Product.objects.all().delete()
        ProductStock.objects.all().delete()
        StockTransaction.objects.all().delete()
        ProductReport.objects.all().delete()
        TestScript.tearDown(self)
