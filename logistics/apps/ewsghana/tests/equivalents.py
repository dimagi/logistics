from rapidsms.tests.scripted import TestScript
from logistics.apps.logistics.models import SupplyPoint, \
    SupplyPointType, Product, ProductType, ProductStock
from logistics.apps.ewsghana.tests.util import load_test_data

class TestEquivalents(TestScript):
    def setUp(self):
        TestScript.setUp(self)
        load_test_data()

    def testLowStock(self):
        a = """
              123 > register stella dedh
              123 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
              123 > ov2
              123 < Dear stella, the following items need to be reordered: ov. Please place an order now.
            """
        self.runScript(a)

    def testEquivalentStockout(self):
        a = """
              123 > register stella dedh
              123 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
              123 > ov0 ml1
              123 < Dear stella, the following items are stocked out: ov. the following items need to be reordered: ml. Please place an order now.
              123 > ov1 ml0
              123 < Dear stella, the following items are stocked out: ml. the following items need to be reordered: ov. Please place an order now.
              123 > ov0 ml20
              123 < Dear stella, thank you for reporting the commodities you have in stock.
              123 > ov20 ml0
              123 < Dear stella, thank you for reporting the commodities you have in stock.
            """
        self.runScript(a)

    def testEquivalentLowSupply(self):
        a = """
              123 > register stella dedh
              123 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
              123 > ov1 ml20
              123 < Dear stella, thank you for reporting the commodities you have in stock.
              123 > ov20 ml1
              123 < Dear stella, thank you for reporting the commodities you have in stock.
              123 > ml20 ov1
              123 < Dear stella, thank you for reporting the commodities you have in stock.
              123 > ml1 ov20
              123 < Dear stella, thank you for reporting the commodities you have in stock.
            """
        self.runScript(a)

    def testNoProductStock(self):
        ov = Product.objects.get(sms_code='ov')
        zz, created = Product.objects.get_or_create(sms_code='zz', name='Test',
                                                    type=ProductType.objects.all()[0], 
                                                    units='cycle')
        zz.equivalents.add(ov)
        a = """
              123 > register stella dedh
              123 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
              123 > ov1 zz20
              123 < Dear stella, the following items need to be reordered: ov. Please place an order now.
              123 > ov20 zz1
              123 < Dear stella, thank you for reporting the commodities you have in stock.
              123 > zz20 ov1
              123 < Dear stella, the following items need to be reordered: ov. Please place an order now.
              123 > zz1 ov20
              123 < Dear stella, thank you for reporting the commodities you have in stock.
            """
        self.runScript(a)

    def testNoConsumption(self):
        ov = Product.objects.get(sms_code='ov')
        dedh = SupplyPoint.objects.get(code='dedh')
        zz, created = Product.objects.get_or_create(sms_code='zz', name='Test',
                                                    type=ProductType.objects.all()[0], 
                                                    units='cycle')
        zz.equivalents.add(ov)
        ProductStock.objects.get_or_create(product=zz, supply_point=dedh)
        a = """
              123 > register stella dedh
              123 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
              123 > ov1 zz20
              123 < Dear stella, the following items need to be reordered: ov. Please place an order now.
              123 > ov20 zz1
              123 < Dear stella, thank you for reporting the commodities you have in stock.
              123 > zz20 ov1
              123 < Dear stella, the following items need to be reordered: ov. Please place an order now.
              123 > zz1 ov20
              123 < Dear stella, thank you for reporting the commodities you have in stock.
            """
        self.runScript(a)
