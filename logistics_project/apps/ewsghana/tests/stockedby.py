from rapidsms.conf import settings
from rapidsms.tests.scripted import TestScript
from logistics.models import Product, ProductStock, \
    SupplyPoint, SupplyPointType, Location
from logistics_project.apps.ewsghana import app as logistics_app
from logistics_project.apps.ewsghana.tests.util import register_user

class TestStockOnHand (TestScript):
    apps = ([logistics_app.App])
    fixtures = ["ghana_initial_data.json"] 
    def setUp(self):
        TestScript.setUp(self)
        location = Location.objects.get(code='de')
        facilitytype = SupplyPointType.objects.get(code='hc')
        facility, created = SupplyPoint.objects.get_or_create(code='dedh',
                                        name='Dangme East District Hospital',
                                        location=location, active=True,
                                        type=facilitytype, supplied_by=None)
        mc = Product.objects.get(sms_code='mc')
        lf = Product.objects.get(sms_code='lf')
        mg = Product.objects.get(sms_code='mg')
        ng = Product.objects.get(sms_code='ng')
        ProductStock(is_active=True, product=mc, supply_point=facility,
                     monthly_consumption=5).save()
        ProductStock(is_active=True, product=lf, supply_point=facility,
                     monthly_consumption=5).save()
        ProductStock(is_active=True, product=mg, supply_point=facility,
                     monthly_consumption=5).save()
        ProductStock(is_active=False, product=ng, supply_point=facility,
                     monthly_consumption=5).save()
        contact = register_user(self, "888", "testuser", "dedh")
        contact.commodities.add(mc)
        contact.commodities.add(lf)

    def testStockByUser(self):
        settings.LOGISTICS_STOCKED_BY = 'user'
        a = """
           888 > soh mc 10
           888 < Dear testuser, still missing lf.
           """
        self.runScript(a)

    def testStockByFacility(self):
        settings.LOGISTICS_STOCKED_BY = 'facility'
        a = """
           888 > soh mc 10
           888 < Dear testuser, still missing lf, mg.
           """
        self.runScript(a)

    def testStockByProduct(self):
        settings.LOGISTICS_STOCKED_BY = 'product'
        a = """
           888 > soh mc 10
           888 < Dear testuser, still missing aa, lf, fr, sp, qu, ad, nv, cb, lm, al, ng, rd, jd, cu, oq, mg, ns, dp, zs.
           """
        self.runScript(a)

    def tearDown(self):
        ProductStock.objects.all().delete()
        TestScript.tearDown(self)
