from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
from logistics.apps.logistics import app as logistics_app
from logistics.apps.logistics.models import ProductReportType, \
    ProductStock, SupplyPoint, Product
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.util import config

class TestLocation (TestScript):
    apps = ([logistics_app.App])
    fixtures = ["ghana_initial_data.json"] 

    def setUp(self):
        TestScript.setUp(self)

    def testLocations(self):
        product = Product.objects.get(sms_code='lf')
        facility = SupplyPoint.objects.all()[0]
        soh = ProductReportType.objects.get(code=Reports.SOH)
        npr = facility.report(product, soh, 3)
        self.assertEquals(npr.quantity, 3)
        self.assertEquals(ProductStock.objects.get(supply_point=facility, product=product).quantity, 3)
        
