from datetime import timedelta
from logistics.const import Reports
from rapidsms.tests.scripted import TestScript
from logistics.models import Location, SupplyPointType, SupplyPoint, \
    Product, ProductType, ProductStock, StockTransaction, ProductReport, ProductReportType
from logistics.models import SupplyPoint as Facility
from logistics.tests.util import load_test_data

class TestConsumption (TestScript):
    fixtures = ["ghana_initial_data.json"]
    
    def setUp(self):
        TestScript.setUp(self)
        load_test_data()

    def testConsumption(self):
        pr = Product.objects.all()[0]
        sp = Facility.objects.all()[0]
        sp.report_stock(pr, 200)
        ps = ProductStock.objects.get(supply_point=sp,product=pr)
        ps.use_auto_consumption = True

        # Not enough data.
        self.assertEquals(None, ps.daily_consumption)
        self.assertEquals(ps.product.average_monthly_consumption, ps.monthly_consumption) #fallback

        ps.monthly_consumption = 999

        st = StockTransaction.objects.get(supply_point=sp,product=pr)
        st.date = st.date - timedelta(days=5)
        st.save()
        sp.report_stock(pr, 150)

        # 5 days still aren't enough to compute.
        self.assertEquals(None, ps.daily_consumption)
        self.assertEquals(ps.monthly_consumption, ps.monthly_consumption)

        sta = StockTransaction.objects.filter(supply_point=sp,product=pr)
        for st in sta:
            st.date = st.date - timedelta(days=5)
            st.save()
        sp.report_stock(pr, 100)

        # 10 days is enough.
        self.assertEquals(10, ps.daily_consumption)
        self.assertEquals(300, ps.monthly_consumption)

        sta = StockTransaction.objects.filter(supply_point=sp,product=pr)
        for st in sta:
            st.date = st.date - timedelta(days=10)
            st.save()
        sp.report_stock(pr, 50)

        # Another data point.
        self.assertEquals(7, ps.daily_consumption)

        sta = StockTransaction.objects.filter(supply_point=sp,product=pr)
        for st in sta:
            st.date = st.date - timedelta(days=10)
            st.save()
        sp.report_stock(pr, 100)

        # Reporting higher stock shouldn't change the daily consumption metric.        
        self.assertEquals(7, ps.daily_consumption)

        npr = ProductReport(product=pr, report_type=ProductReportType.objects.get(code=Reports.REC),
                            quantity=10000, message=None, supply_point=sp)
        npr.save()
        # Make sure receipts don't change the daily consumption
        self.assertEquals(7, ps.daily_consumption)
