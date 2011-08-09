from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user, add_products
from logistics.apps.logistics.models import Product, ProductStock

class TestDelivery(TanzaniaTestScriptBase):
        
    def setUp(self):
        super(TestDelivery, self).setUp()
        ProductStock.objects.all().delete()
        
    def testDelivery(self):
        contact = register_user(self, "778", "someone")
        add_products(contact, ["id", "dp", "ip"])
        
        script = """
            778 > nimepokea Id 400 Dp 569 Ip 678
            778 < Asante %(contact_name)s kwa kutuma taarifa ya kupokea vifaa vya %(facility_name)s
        """ % {'contact_name': contact.name, 'facility_name': 'changeme'}
        self.runScript(script)
        self.assertEqual(3, ProductStock.objects.count())
        for ps in ProductStock.objects.all():
            self.assertEqual(contact.supply_point, ps.supply_point)
            self.assertTrue(0 != ps.quantity)        