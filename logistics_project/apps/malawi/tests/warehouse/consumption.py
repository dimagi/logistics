from datetime import datetime, timedelta
from rapidsms.conf import settings
from rapidsms.tests.scripted import TestScript
from logistics.models import Location, SupplyPointType, SupplyPoint, \
    Product, ProductType, ProductStock, StockTransaction, ProductReport, \
    ProductReportType, DefaultMonthlyConsumption
from logistics.models import SupplyPoint as Facility
from logistics.tests.util import fake_report
from logistics.const import Reports
from logistics_project.apps.malawi.warehouse.models import Consumption
from logistics_project.apps.malawi.tests.base import MalawiTestBase
from logistics_project.apps.malawi.warehouse.runner import update_consumption_values

SECONDS = 60 * 60 * 24

class TestConsumption(MalawiTestBase):
        
    def setUp(self):
        super(TestConsumption, self).setUp()
        self.pr = Product.objects.all()[0]
        self.sp = Facility.objects.all()[0]
        Consumption.objects.all().delete()
        StockTransaction.objects.all().delete()
        
    def _report(self, amount, date, report_type):
        return fake_report(self.sp, self.pr, amount, None, report_type, date)
        
    def _consumption_qs(self):
        return Consumption.objects.filter(supply_point=self.sp,
                                          product=self.pr).order_by("date")
    
    def testSingleReportDoesNothing(self):
        self._report(100, datetime(2012, 8, 1), Reports.SOH)
        update_consumption_values(StockTransaction.objects.all())
        # nothing happens with only 1 data point
        self.assertEqual(0, self._consumption_qs().count())
    
    def testSameValueDoesNothing(self):
        self._report(100, datetime(2012, 8, 1), Reports.SOH)
        self._report(100, datetime(2012, 8, 11), Reports.SOH)
        self._report(100, datetime(2012, 8, 21), Reports.SOH)
        update_consumption_values(StockTransaction.objects.all())
        [c] = self._consumption_qs()
        self.assertEqual(0, c.calculated_consumption)
        self.assertEqual(0, c.time_stocked_out)
        
    def testProlongedStockouts(self):
        self._report(0, datetime(2012, 8, 1), Reports.SOH)
        self._report(0, datetime(2012, 8, 11), Reports.SOH)
        self._report(0, datetime(2012, 8, 21), Reports.SOH)
        update_consumption_values(StockTransaction.objects.all())
        [c] = self._consumption_qs()
        self.assertEqual(0, c.calculated_consumption)
        self.assertEqual(20 * SECONDS, c.time_stocked_out)
        
    def testConsumptionInSingleMonth(self):
        t, ps = self._report(100, datetime(2012, 8, 1), Reports.SOH)
        update_consumption_values(StockTransaction.objects.filter(pk=t.pk))
        
        t, ps = self._report(50, datetime(2012, 8, 11), Reports.SOH)
        update_consumption_values(StockTransaction.objects.filter(pk=t.pk))
        
        [c] = self._consumption_qs()
        self.assertEqual(50, c.calculated_consumption)
        self.assertEqual(0, c.time_stocked_out)
        
        t, ps = self._report(0, datetime(2012, 8, 21), Reports.SOH)
        update_consumption_values(StockTransaction.objects.filter(pk=t.pk))
        
        [c] = self._consumption_qs()
        self.assertEqual(100, c.calculated_consumption)
        self.assertEqual(0, c.time_stocked_out)
        
        t, ps = self._report(100, datetime(2012, 8, 25), Reports.SOH)
        update_consumption_values(StockTransaction.objects.filter(pk=t.pk))
        
        [c] = self._consumption_qs()
        self.assertEqual(100, c.calculated_consumption)
        self.assertEqual(4 * SECONDS, c.time_stocked_out)
        
        # for good measure, clear everything and try again
        Consumption.objects.all().delete()
        update_consumption_values(StockTransaction.objects.all())
        [c] = self._consumption_qs()
        self.assertEqual(100, c.calculated_consumption)
        self.assertEqual(4 * SECONDS, c.time_stocked_out)
    
    def testConsumptionInConsecutiveMonths(self):
        # 50 in july, 50 in aug
        self._report(500, datetime(2012, 8, 1) - timedelta(days=5), Reports.SOH)
        self._report(450, datetime(2012, 8, 1) + timedelta(days=5),  Reports.SOH)
        update_consumption_values(StockTransaction.objects.all())
        c1, c2 = self._consumption_qs()
        self.assertEqual(25, c1.calculated_consumption)
        self.assertEqual(25, c2.calculated_consumption)
        
        # 100 in aug
        t, ps = self._report(350, datetime(2012, 9, 1) - timedelta(days=5),  Reports.SOH)
        update_consumption_values(StockTransaction.objects.filter(pk=t.pk))
        c1, c2 = self._consumption_qs()
        self.assertEqual(25, c1.calculated_consumption)
        self.assertEqual(125, c2.calculated_consumption)
        
        # 50 in aug, 100 in sept
        t, ps = self._report(200, datetime(2012, 9, 1) + timedelta(days=10),  Reports.SOH)
        update_consumption_values(StockTransaction.objects.filter(pk=t.pk))
        c1, c2, c3 = self._consumption_qs()
        self.assertEqual(25, c1.calculated_consumption)
        self.assertEqual(175, c2.calculated_consumption)
        self.assertEqual(100, c3.calculated_consumption)
        
        Consumption.objects.all().delete()
        update_consumption_values(StockTransaction.objects.all())
        c1, c2, c3 = self._consumption_qs()
        self.assertEqual(25, c1.calculated_consumption)
        self.assertEqual(175, c2.calculated_consumption)
        self.assertEqual(100, c3.calculated_consumption)
    
    def testWithReceipts(self):
        self._report(100, datetime(2012, 8, 1), Reports.SOH)
        self._report(100, datetime(2012, 8, 11), Reports.REC)
        self._report(100, datetime(2012, 8, 21), Reports.SOH)
        update_consumption_values(StockTransaction.objects.all())
        [c] = self._consumption_qs()
        self.assertEqual(100, c.calculated_consumption)
        
    