from __future__ import absolute_import
from logistics.models import Product, SupplyPoint, ProductStock

from logistics_project.apps.malawi.tests.util import create_hsa
from logistics_project.apps.malawi.tests.base import MalawiTestBase
from django.conf import settings

class TestProductLevels(MalawiTestBase):
    
    def testEmergencyLevels(self):
        csv_file = open(settings.STATIC_PRODUCTS, 'r')
        try:
            count = 0
            expected_count = Product.objects.exclude(emergency_order_level=None).count()
            static_sp = SupplyPoint.objects.all()[0]
            self.assertTrue(expected_count > 0) # make sure we wil check something
            for line in csv_file:
                # leave out first line
                if "product name" in line.lower():
                    continue
                #Product Name,Code,Dose,AMC,Family,Formulation,EOP Quantity,# of patients a month,
                name, code, dose, monthly_consumption, typename, form, eop_quant, num_pats = line.strip().split(",")
                try:
                    eo = int(eop_quant)
                    product = Product.objects.get(sms_code__iexact=code)
                    self.assertEqual(eo, product.emergency_order_level)
                    ps = ProductStock.objects.create(supply_point=static_sp, product=product)
                    self.assertEqual(ps.emergency_reorder_level, eo)
                    count = count + 1
                except ValueError:
                    pass
            self.assertEqual(count, expected_count) # make sure we checked enough
        finally:
            csv_file.close()
    
class TestAddRemoveProducts(MalawiTestBase):
    
    def testAddRemoveProduct(self):

        a = """
           16175551234 > add zi
           16175551234 < Sorry, you have to be registered with the system to do that. For help, please contact your supervisor
        """
        self.runScript(a)

        hsa = create_hsa(self, "16175551234", "stella")

        self.assertFalse(hsa.supply_point.supplies_product(Product.objects.get(sms_code="zi")))
        self.assertFalse(Product.objects.get(sms_code="zi") in hsa.commodities.all())


        a = """
           16175551234 > add quux
           16175551234 < Sorry, no product matches code quux.  Nothing done.
           16175551234 > add zi
           16175551234 < Thank you, you now supply: zi
        """
        self.runScript(a)

        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="zi")))
        self.assertTrue(Product.objects.get(sms_code="zi") in hsa.commodities.all())

        b = """
           16175551234 > add zi de dm
           16175551234 < Thank you, you now supply: de dm zi
        """
        self.runScript(b)


        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="zi")))
        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="de")))
        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="dm")))
        self.assertFalse(hsa.supply_point.supplies_product(Product.objects.get(sms_code="cm")))

        c = """
           16175551234 > remove cm
           16175551234 < Done. You now supply: de dm zi
           16175551234 > remove de
           16175551234 < Done. You now supply: dm zi
           """
        self.runScript(c)

        self.assertFalse(Product.objects.get(sms_code="cm") in hsa.commodities.all())
        self.assertFalse(Product.objects.get(sms_code="de") in hsa.commodities.all())

        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="zi")))
        self.assertFalse(hsa.supply_point.supplies_product(Product.objects.get(sms_code="de")))
        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="dm")))
        self.assertFalse(hsa.supply_point.supplies_product(Product.objects.get(sms_code="cm")))
