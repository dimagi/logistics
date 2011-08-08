from logistics.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics.apps.tanzania.tests.util import register_user, add_products
from logistics.apps.logistics.models import Product, ProductStock

class TestStockouts(TanzaniaTestScriptBase):
        
    def setUp(self):
        super(TestStockouts, self).setUp()
        ProductStock.objects.all().delete()
        
    def testStockout(self):
        contact = register_user(self, "778", "someone")
        add_products(contact, ["id", "dp", "ip"])
        script = """
            778 > Hmk Id 400 Dp 569 Ip 678
            778 < Asante, umetoa taarifa una dp,id,ip. Kama sio sahihi, tafadhali tuma tena taarifa sahihi.
        """
        self.runScript(script)
        self.assertEqual(3, ProductStock.objects.count())
        for ps in ProductStock.objects.all():
            self.assertEqual(contact.supply_point, ps.supply_point)
            self.assertTrue(0 != ps.quantity)
        
        script = """
            778 > stockout id dp ip
            778 < Asante someone kwa kutuma taarifa ya hakuna dp id ip vya VETA 1.
        """
        self.runScript(script)
        for ps in ProductStock.objects.all():
            self.assertEqual(contact.supply_point, ps.supply_point)
            self.assertEqual(0, ps.quantity)
            
        
