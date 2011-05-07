from datetime import timedelta
from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
from logistics.apps.logistics import app as logistics_app
from logistics.apps.logistics.models import Location, Facility, SupplyPointType, SupplyPoint, Product, ProductStock, StockTransaction

class TestConsumption (TestScript):
    apps = ([logistics_app.App])
    fixtures = ["ghana_initial_data.json"]

    def testConsumption(self):
        if not SupplyPoint.objects.exists():
            location = Location.objects.get(code='de')
            facilitytype = SupplyPointType.objects.get(code='hc')
            rms = Facility.objects.get(code='garms')
            sp, created = Facility.objects.get_or_create(code='dedh',
                                                           name='Dangme East District Hospital',
                                                           location=location, active=True,
                                                           type=facilitytype, supplied_by=rms)
        else:
            sp = SupplyPoint.objects.all()[0]
        pr = Product.objects.all()[0]
        sp.report_stock(pr, 200)
        ps = ProductStock.objects.get(supply_point=sp,product=pr)

        # Not enough data.
        self.assertEquals(None, ps.daily_consumption)
        self.assertEquals(ps.product.average_monthly_consumption, ps.monthly_consumption) #fallback

        ps.base_monthly_consumption = 999

        st = StockTransaction.objects.get(supply_point=sp,product=pr)
        st.date = st.date - timedelta(days=5)
        st.save()
        sp.report_stock(pr, 150)

        # 5 days still aren't enough to compute.
        self.assertEquals(None, ps.daily_consumption)
        self.assertEquals(ps.base_monthly_consumption, ps.base_monthly_consumption)

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
        