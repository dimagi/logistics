from __future__ import absolute_import
from logistics.apps.logistics.models import Product

from logistics.apps.malawi.tests.util import create_hsa
from logistics.apps.malawi.tests.base import MalawiTestBase

class TestAddRemoveProducts(MalawiTestBase):
    
    def testAddRemoveProduct(self):

        a = """
           16175551234 > add zi
           16175551234 < Sorry, you have to be registered with the system to do that. For help, please contact your supervisor
        """
        self.runScript(a)

        hsa = create_hsa(self, "16175551234", "stella")

        self.assertFalse(hsa.supply_point.supplies_product(Product.objects.get(sms_code="zi")))

        a = """
           16175551234 > add quux
           16175551234 < Sorry, no product matches code quux.  Nothing done.
           16175551234 > add zi
           16175551234 < Thank you, you now supply: zi
        """
        self.runScript(a)

        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="zi")))

        b = """
           16175551234 > add zi de dm
           16175551234 < Thank you, you now supply: zi de dm
        """
        self.runScript(b)


        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="zi")))
        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="de")))
        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="dm")))
        self.assertFalse(hsa.supply_point.supplies_product(Product.objects.get(sms_code="cm")))

        c = """
           16175551234 > remove cm
           16175551234 < Done. You now supply: zi de dm
           16175551234 > remove de
           16175551234 < Done. You now supply: zi dm
           """
        self.runScript(c)

        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="zi")))
        self.assertFalse(hsa.supply_point.supplies_product(Product.objects.get(sms_code="de")))
        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="dm")))
        self.assertFalse(hsa.supply_point.supplies_product(Product.objects.get(sms_code="cm")))
