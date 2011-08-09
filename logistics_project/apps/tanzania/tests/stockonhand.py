from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user, add_products
from logistics.apps.logistics.models import Product, ProductStock

class TestStockOnHand(TanzaniaTestScriptBase):
        
    def setUp(self):
        super(TestStockOnHand, self).setUp()
        ProductStock.objects.all().delete()
        
    def testStockOnHand(self):
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
        
    def testsStockOnHandPartialReport(self):
        contact = register_user(self, "778", "someone")
        add_products(contact, ["id", "dp", "ip"])
        script = """
            778 > Hmk Id 400 
            778 < Asante someone kwa kutuma taarifa za akiba ya vifaa vilivyopo vya VETA 1, bado taarifa za dp ip
        """
        self.runScript(script)
        
        script = """
            778 > Hmk Dp 569
            778 < Asante someone kwa kutuma taarifa za akiba ya vifaa vilivyopo vya VETA 1, bado taarifa za ip
        """
        self.runScript(script)
        
        script = """
            778 > Hmk Ip 678
            778 < Asante, umetoa taarifa una ip. Kama sio sahihi, tafadhali tuma tena taarifa sahihi.
        """
        self.runScript(script)
        