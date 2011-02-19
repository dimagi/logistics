from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
import logistics.apps.logistics.app as logistics_app
from logistics.apps.logistics.models import ProductStockReport, ProductReportType, \
    ProductStock, Product, Location, STOCK_ON_HAND_REPORT_TYPE

class TestLocation (TestScript):
    apps = ([logistics_app.App])

    def setUp(self):
        TestScript.setUp(self)

    def testProductStockReport(self):
        product = Product.objects.get(sms_code='lf')
        location = Location.objects.all()[0]
        soh = ProductReportType.objects.get(slug=STOCK_ON_HAND_REPORT_TYPE)
        npr = location.report(product, soh, 3)
        self.assertEquals(npr.quantity, 3)
        self.assertEquals(ProductStock.objects.get(location=location, product=product).quantity, 3)
        