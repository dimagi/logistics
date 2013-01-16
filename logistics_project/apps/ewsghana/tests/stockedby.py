from datetime import datetime, timedelta
from rapidsms.conf import settings
from rapidsms.tests.scripted import TestScript
from logistics.models import Product, ProductStock, \
    SupplyPoint, SupplyPointType, Location
from logistics_project.apps.ewsghana import app as logistics_app
from logistics_project.apps.ewsghana.tests.util import register_user

class TestStockedBy (TestScript):
    apps = ([logistics_app.App])
    fixtures = ["ghana_initial_data.json"] 
    def setUp(self):
        TestScript.setUp(self)
        location = Location.objects.get(code='de')
        facilitytype = SupplyPointType.objects.get(code='hc')
        self.facility, created = SupplyPoint.objects.get_or_create(code='dedh',
                                        name='Dangme East District Hospital',
                                        location=location, active=True,
                                        type=facilitytype, supplied_by=None)
        self.mc = Product.objects.get(sms_code='mc')
        self.lf = Product.objects.get(sms_code='lf')
        self.mg = Product.objects.get(sms_code='mg')
        self.ng = Product.objects.get(sms_code='ng')
        contact = register_user(self, "888", "testuser", "dedh")
        contact.commodities.add(self.mc)
        contact.commodities.add(self.lf)

    def testStockByUser(self):
        ProductStock.objects.all().delete()
        settings.LOGISTICS_STOCKED_BY = 'user'
        a = """
           888 > soh mc 10
           888 < Dear testuser, still missing lf.
           """
        self.runScript(a)

    def testStockByFacility(self):
        ProductStock.objects.all().delete()
        ProductStock(is_active=True, product=self.mc, supply_point=self.facility,
                     monthly_consumption=5, last_modified=datetime.now() - timedelta(days=30)).save()
        ProductStock(is_active=True, product=self.lf, supply_point=self.facility,
                     monthly_consumption=5, last_modified=datetime.now() - timedelta(days=30)).save()
        ProductStock(is_active=True, product=self.mg, supply_point=self.facility,
                     monthly_consumption=5, last_modified=datetime.now() - timedelta(days=30)).save()
        settings.LOGISTICS_STOCKED_BY = 'facility'
        a = """
           888 > soh mc 10
           888 < Dear testuser, still missing lf, mg.
           """
        self.runScript(a)

    def testStockByProduct(self):
        ProductStock.objects.all().delete()
        settings.LOGISTICS_STOCKED_BY = 'product'
        a = """
           888 > soh mc 10
           888 < Dear testuser, still missing aa, lf, fr, sp, qu, ad, nv, cb, lm, al, ng, rd, jd, cu, oq, mg, ns, dp, zs.
           """
        self.runScript(a)

    def tearDown(self):
        ProductStock.objects.all().delete()
        TestScript.tearDown(self)
