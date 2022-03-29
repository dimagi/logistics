from __future__ import unicode_literals
from datetime import datetime, timedelta
from logistics.models import Product, StockTransaction
from logistics.models import SupplyPoint as Facility
from logistics.tests.util import fake_report
from logistics.const import Reports
from logistics_project.apps.malawi.warehouse.models import CalculatedConsumption
from logistics_project.apps.malawi.tests.base import MalawiTestBase
from logistics_project.apps.malawi.warehouse.runner import update_consumption_values

SECONDS = 60 * 60 * 24

class TestConsumption(MalawiTestBase):
        
    def setUp(self):
        super(TestConsumption, self).setUp()
        self.pr = Product.objects.all()[0]
        self.sp = Facility.objects.all()[0]
        CalculatedConsumption.objects.all().delete()
        StockTransaction.objects.all().delete()
        
    def _report(self, amount, date, report_type):
        return fake_report(self.sp, self.pr, amount, None, report_type, date)
        
    def _consumption_qs(self):
        return CalculatedConsumption.objects.filter(supply_point=self.sp,
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
        self.assertEqual(10 * SECONDS, c.time_with_data)
        
        t, ps = self._report(0, datetime(2012, 8, 21), Reports.SOH)
        update_consumption_values(StockTransaction.objects.filter(pk=t.pk))
        
        [c] = self._consumption_qs()
        self.assertEqual(100, c.calculated_consumption)
        self.assertEqual(0, c.time_stocked_out)
        self.assertEqual(20 * SECONDS, c.time_with_data)
        
        t, ps = self._report(100, datetime(2012, 8, 25), Reports.REC)
        update_consumption_values(StockTransaction.objects.filter(pk=t.pk))
        
        [c] = self._consumption_qs()
        self.assertEqual(100, c.calculated_consumption)
        self.assertEqual(4 * SECONDS, c.time_stocked_out)
        self.assertEqual(24 * SECONDS, c.time_with_data)
        
        # for good measure, clear everything and try again
        CalculatedConsumption.objects.all().delete()
        update_consumption_values(StockTransaction.objects.all())
        [c] = self._consumption_qs()
        self.assertEqual(100, c.calculated_consumption)
        self.assertEqual(4 * SECONDS, c.time_stocked_out)
        self.assertEqual(24 * SECONDS, c.time_with_data)
        
    def testConsumptionInConsecutiveMonths(self):
        # 50 in july, 50 in aug
        self._report(500, datetime(2012, 8, 1) - timedelta(days=5), Reports.SOH)
        self._report(450, datetime(2012, 8, 1) + timedelta(days=5),  Reports.SOH)
        update_consumption_values(StockTransaction.objects.all())
        c1, c2 = self._consumption_qs()
        self.assertEqual(25, c1.calculated_consumption)
        self.assertEqual(25, c2.calculated_consumption)
        self.assertEqual(5 * SECONDS, c1.time_with_data)
        self.assertEqual(5 * SECONDS, c2.time_with_data)
        
        # 100 in aug
        t, ps = self._report(350, datetime(2012, 9, 1) - timedelta(days=5),  Reports.SOH)
        update_consumption_values(StockTransaction.objects.filter(pk=t.pk))
        c1, c2 = self._consumption_qs()
        self.assertEqual(25, c1.calculated_consumption)
        self.assertEqual(125, c2.calculated_consumption)
        self.assertEqual(5 * SECONDS, c1.time_with_data)
        self.assertEqual(26 * SECONDS, c2.time_with_data)
        
        # 50 in aug, 100 in sept
        t, ps = self._report(200, datetime(2012, 9, 1) + timedelta(days=10),  Reports.SOH)
        update_consumption_values(StockTransaction.objects.filter(pk=t.pk))
        c1, c2, c3 = self._consumption_qs()
        self.assertEqual(25, c1.calculated_consumption)
        self.assertEqual(175, c2.calculated_consumption)
        self.assertEqual(100, c3.calculated_consumption)
        self.assertEqual(5 * SECONDS, c1.time_with_data)
        self.assertEqual(31 * SECONDS, c2.time_with_data)
        self.assertEqual(10 * SECONDS, c3.time_with_data)
        
        CalculatedConsumption.objects.all().delete()
        update_consumption_values(StockTransaction.objects.all())
        c1, c2, c3 = self._consumption_qs()
        self.assertEqual(25, c1.calculated_consumption)
        self.assertEqual(175, c2.calculated_consumption)
        self.assertEqual(100, c3.calculated_consumption)
        self.assertEqual(5 * SECONDS, c1.time_with_data)
        self.assertEqual(31 * SECONDS, c2.time_with_data)
        self.assertEqual(10 * SECONDS, c3.time_with_data)
        
    def testConsumptionAcrossMultipleMonths(self):
        # 50 in july, 310 in aug, rest in sept
        self._report(600, datetime(2012, 8, 1) - timedelta(days=5), Reports.SOH)
        self._report(100, datetime(2012, 8, 1) + timedelta(days=45),  Reports.SOH)
        update_consumption_values(StockTransaction.objects.all())
        c1, c2, c3 = self._consumption_qs()
        self.assertEqual(50, c1.calculated_consumption)
        self.assertEqual(310, c2.calculated_consumption)
        self.assertEqual(140, c3.calculated_consumption)
        self.assertEqual(5 * SECONDS, c1.time_with_data)
        self.assertEqual(31 * SECONDS, c2.time_with_data)
        self.assertEqual(14 * SECONDS, c3.time_with_data)
        
    def testStockoutAcrossMonths(self):
        self._report(0, datetime(2012, 8, 1) - timedelta(days=6), Reports.SOH)
        self._report(100, datetime(2012, 8, 1) + timedelta(days=9),  Reports.REC)
        update_consumption_values(StockTransaction.objects.all())
        c1, c2 = self._consumption_qs()
        self.assertEqual(0, c1.calculated_consumption)
        self.assertEqual(0, c2.calculated_consumption)
        self.assertEqual(6 * SECONDS, c1.time_with_data)
        self.assertEqual(9 * SECONDS, c2.time_with_data)
        self.assertEqual(6 * SECONDS, c1.time_stocked_out)
        self.assertEqual(9 * SECONDS, c2.time_stocked_out)
        
        
    def testWithReceipts(self):
        self._report(100, datetime(2012, 8, 1), Reports.SOH)
        self._report(100, datetime(2012, 8, 11), Reports.REC)
        self._report(100, datetime(2012, 8, 21), Reports.SOH)
        update_consumption_values(StockTransaction.objects.all())
        [c] = self._consumption_qs()
        self.assertEqual(100, c.calculated_consumption)

    def testAnomalousData(self):
        t, ps = self._report(100, datetime(2012, 8, 1), Reports.SOH)
        update_consumption_values(StockTransaction.objects.filter(pk=t.pk))
        
        t, ps = self._report(50, datetime(2012, 8, 11), Reports.SOH)
        update_consumption_values(StockTransaction.objects.filter(pk=t.pk))
        
        [c] = self._consumption_qs()
        self.assertEqual(10 * SECONDS, c.time_with_data)
        
        # anomalous!
        t, ps = self._report(150, datetime(2012, 8, 21), Reports.SOH)
        update_consumption_values(StockTransaction.objects.filter(pk=t.pk))
        [c] = self._consumption_qs()
        self.assertEqual(10 * SECONDS, c.time_with_data)
        
        # ok
        t, ps = self._report(100, datetime(2012, 8, 25), Reports.SOH)
        update_consumption_values(StockTransaction.objects.filter(pk=t.pk))
        
        [c] = self._consumption_qs()
        self.assertEqual(14 * SECONDS, c.time_with_data)
        
        # for good measure, clear everything and try again
        CalculatedConsumption.objects.all().delete()
        update_consumption_values(StockTransaction.objects.all())
        [c] = self._consumption_qs()
        self.assertEqual(14 * SECONDS, c.time_with_data)
        
        
    