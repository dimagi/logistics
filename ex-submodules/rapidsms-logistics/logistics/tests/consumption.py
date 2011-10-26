from datetime import timedelta
from logistics.const import Reports
from rapidsms.tests.scripted import TestScript
from logistics.models import Location, SupplyPointType, SupplyPoint, \
    Product, ProductType, ProductStock, StockTransaction, ProductReport, ProductReportType
from logistics.models import SupplyPoint as Facility
from logistics.tests.util import load_test_data
from logistics.const import Reports

class TestConsumption (TestScript):
    def setUp(self):
        TestScript.setUp(self)
        load_test_data()
        self.pr = Product.objects.all()[0]
        self.sp = Facility.objects.all()[0]
        self.ps = ProductStock.objects.get(supply_point=self.sp, product=self.pr)
        self.ps.use_auto_consumption = True
        self.ps.save

    def testConsumption(self):
        self.sp.report_stock(self.pr, 200) 

        # Not enough data.
        self.assertEquals(None, self.ps.daily_consumption)
        self.assertEquals(self.ps.product.average_monthly_consumption, self.ps.monthly_consumption) #fallback

        self.ps.monthly_consumption = 999

        st = StockTransaction.objects.get(supply_point=self.sp,product=self.pr)
        st.date = st.date - timedelta(days=5)
        st.save()
        self.sp.report_stock(self.pr, 150)

        # 5 days still aren't enough to compute.
        self.assertEquals(None, self.ps.daily_consumption)
        self.assertEquals(self.ps.monthly_consumption, self.ps.monthly_consumption)

        sta = StockTransaction.objects.filter(supply_point=self.sp,product=self.pr)
        for st in sta:
            st.date = st.date - timedelta(days=5)
            st.save()
        self.sp.report_stock(self.pr, 100)

        # 10 days is enough.
        self.assertEquals(10, self.ps.daily_consumption) # 200 in stock 10 days ago, 150 in stock 5 days ago
        self.assertEquals(300, self.ps.monthly_consumption)

        sta = StockTransaction.objects.filter(supply_point=self.sp,product=self.pr)
        for st in sta:
            st.date = st.date - timedelta(days=10)
            st.save()
        self.sp.report_stock(self.pr, 50) # 200 in stock 20 days ago, 150 in stock 15 days ago, 50 in stock now

        # Another data point.
        self.assertEquals(7.5, round(self.ps.daily_consumption, 1))
        # Make sure the rounding is correct
        self.assertEquals(225, round(self.ps.monthly_consumption))

        sta = StockTransaction.objects.filter(supply_point=self.sp,product=self.pr)
        for st in sta:
            st.date = st.date - timedelta(days=10)
            st.save()
        self.sp.report_stock(self.pr, 100)

        # Reporting higher stock shouldn't change the daily consumption
        # since we have no way of knowing how much was received vs dispensed.
        self.assertEquals(7.5, round(self.ps.daily_consumption, 1))

        npr = ProductReport(product=self.pr, report_type=ProductReportType.objects.get(code=Reports.REC),
                            quantity=10000, message=None, supply_point=self.sp)
        npr.save()
        
        # Make sure receipts after a soh report don't change the daily consumption
        # since we don't know what the new balance is. Only change consumption 
        # when we get the soh report after the receipt.
        self.assertEquals(7.5, round(self.ps.daily_consumption, 1))

    def testConsumptionWithMultipleReports(self):
        self.ps = ProductStock.objects.get(supply_point=self.sp, 
                                           product=self.pr)
        self.ps.use_auto_consumption = True
        self.ps.save()
                    
        self._report(40, 60, Reports.SOH) # 60 days ago we had 40 in stock. 
        self.assertEquals(None, self.ps.daily_consumption)

        self._report(30, 50, Reports.REC) # 50 days ago, we received 30
        self.assertEquals(None, self.ps.daily_consumption) # consumption unchanged

        self._report(20, 50, Reports.SOH) # 50 days ago, we had 20 in stock (so we've consumed 50)
        self.assertEquals(5, self.ps.daily_consumption) # 50/10 days

        self._report(10, 40, Reports.SOH) # 40 days ago we had 10 in stock (so we've consume 60 over 20 days)
        self.assertEquals(3, self.ps.daily_consumption)

    def testFloatingPointAccuracy(self):
        self._report(10, 51, Reports.REC) 
        self.assertEquals(None, self.ps.daily_consumption) # consumption unchanged

        self._report(50, 50, Reports.SOH) 
        self.assertEquals(None, self.ps.daily_consumption)

        self._report(0, 41, Reports.REC)
        self.assertEquals(None, self.ps.daily_consumption) # consumption unchanged

        self._report(30, 40, Reports.SOH) 
        self.assertEquals(2, round(self.ps.daily_consumption)) # 20/10 days
        self.assertEquals(54, round(self.ps.monthly_consumption))

        self._report(10, 31, Reports.REC) 
        self.assertEquals(2, round(self.ps.daily_consumption)) # consumption unchanged
        self.assertEquals(54, round(self.ps.monthly_consumption))

        self._report(20, 30, Reports.SOH)
        self.assertEquals(2, round(self.ps.daily_consumption)) # 40/20
        self.assertEquals(57, round(self.ps.monthly_consumption))

    def _report(self, amount, days_ago, report_type):
        if report_type == Reports.SOH:
            report = self.sp.report_stock(self.pr, amount)
        else:
            report = self.sp.report_receipt(self.pr, amount)
        try:
            trans = StockTransaction.objects.get(product_report=report)
        except StockTransaction.DoesNotExist:
            return
        trans.date = trans.date - timedelta(days=days_ago)
        trans.save()

    def tearDown(self):
        Location.objects.all().delete()
        SupplyPoint.objects.all().delete()
        Product.objects.all().delete()
        ProductStock.objects.all().delete()
        StockTransaction.objects.all().delete()
        ProductReport.objects.all().delete()
        TestScript.tearDown(self)
