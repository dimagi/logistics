from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
import logistics.apps.logistics.app as logistics_app
from logistics.apps.logistics.models import ProductReportType, \
    ProductStock, Product, Facility, STOCK_ON_HAND_REPORT_TYPE

class TestLocation (TestScript):
    apps = ([logistics_app.App])

    def setUp(self):
        TestScript.setUp(self)

    def testLocations(self):
        product = Product.objects.get(sms_code='lf')
        facility = Facility.objects.all()[0]
        soh = ProductReportType.objects.get(slug=STOCK_ON_HAND_REPORT_TYPE)
        npr = facility.report(product, soh, 3)
        self.assertEquals(npr.quantity, 3)
        self.assertEquals(ProductStock.objects.get(facility=facility, product=product).quantity, 3)
        