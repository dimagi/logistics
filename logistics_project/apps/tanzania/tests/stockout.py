from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user, add_products
from logistics.models import Product, ProductStock
from logistics.util import config
from django.utils import translation
from django.utils.translation import ugettext as _

class TestStockouts(TanzaniaTestScriptBase):
        
    def setUp(self):
        super(TestStockouts, self).setUp()
        ProductStock.objects.all().delete()
        
    def testStockout(self):
        contact = register_user(self, "778", "someone")
        add_products(contact, ["id", "dp", "ip"])
        script = """
            778 > Hmk Id 400 Dp 569 Ip 678
            778 < %(soh_confirm)s
            """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
        self.runScript(script)
        
        self.assertEqual(3, ProductStock.objects.count())
        for ps in ProductStock.objects.all():
            self.assertEqual(contact.supply_point, ps.supply_point)
            self.assertTrue(0 != ps.quantity)
        
        script = """
            778 > stockout id dp ip
            """ % {"stockout_confirm": _(config.Messages.STOCKOUT_CONFIRM) % {"contact_name":"changeme",
                                                                              "product_names":"changeme",
                                                                              "facility_name":"changeme"}}
        self.runScript(script)
        for ps in ProductStock.objects.all():
            self.assertEqual(contact.supply_point, ps.supply_point)
            self.assertEqual(0, ps.quantity)
            
        
