from __future__ import absolute_import
from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
from logistics.apps.logistics.models import Product, ProductStock, \
    ProductReportsHelper, Facility, SupplyPointType, Location, STOCK_ON_HAND_REPORT_TYPE,\
    StockRequest, SupplyPoint
from logistics.apps.malawi import app as malawi_app

class TestStockOnHandMalawi(TestScript):
    apps = ([malawi_app.App])
    fixtures = ["malawi_products.json"]
    
    def setUp(self):
        TestScript.setUp(self)
        StockRequest.objects.all().delete()
    
    def testStockOnHandCreatesRequest(self):
        
        a = """
        
           16175551234 > register stella 1 2616
           16175551234 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Ntaja
           16175551234 > soh zi 10
           16175551234 < Dear stella, the following items need to be reordered: zi. Please place an order now.
           """
        self.runScript(a)
        self.assertEqual(1, StockRequest.objects.count())
        req = StockRequest.objects.all()[0]
        self.assertEqual(req.supply_point, SupplyPoint.objects.get(code="26161"))
        
    