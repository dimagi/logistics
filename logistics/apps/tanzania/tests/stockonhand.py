from logistics.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics.apps.tanzania.tests.util import register_user, add_products
from logistics.apps.logistics.models import Product, ProductStock

class TestRegister(TanzaniaTestScriptBase):
    
    def testStockOnHand(self):
        contact = register_user(self, "778", "someone")
        add_products(contact, ["id", "dp", "ip"])
        script = """
            778 > Hmk Id 400 Dp 569 Ip 678
            778 < Asante, umetoa taarifa una dp,id,ip. Kama sio sahihi, tafadhali tuma tena taarifa sahihi.
        """
        self.runScript(script)