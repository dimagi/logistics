from __future__ import absolute_import
from logistics.models import Product, SupplyPoint, ProductStock

from logistics_project.apps.malawi.tests.util import create_hsa
from logistics_project.apps.malawi.tests.base import MalawiTestBase
from django.conf import settings
from static.malawi.config import BaseLevel, SupplyPointCodes, Messages


class TestProductLevels(MalawiTestBase):
    
    def testStaticLoader(self):
        csv_file = open(settings.STATIC_PRODUCTS, 'r')
        try:
            count = 0
            # EPI Products aren't loaded through the static loader so exclude them here
            expected_count = Product.objects.filter(emergency_order_level__isnull=False, type__base_level=BaseLevel.HSA).count()
            self.assertTrue(expected_count > 0) # make sure we wil check something
            for line in csv_file:
                # leave out first line
                if "product name" in line.lower():
                    continue
                #Product Name,Code,Dose,AMC,Family,Formulation,EOP Quantity,# of patients a month,
                name, code, dose, monthly_consumption, typename, form, eop_quant, num_pats, min_pack_size = line.strip().split(",")
                try:
                    eo = int(eop_quant)
                    product = Product.objects.get(sms_code__iexact=code)
                    self.assertEqual(eo, product.emergency_order_level)
                    count = count + 1
                except ValueError:
                    pass
            self.assertEqual(count, expected_count) # make sure we checked enough
        finally:
            csv_file.close()

    def testEmergencyLevels(self):
        create_hsa(self, "+5551111", "hsa")
        hsa = SupplyPoint.objects.filter(type__code=SupplyPointCodes.HSA)[0]
        for product in Product.objects.filter(type__base_level=BaseLevel.HSA):
            ps = ProductStock.objects.create(supply_point=hsa, product=product)
            self.assertEqual(ps.emergency_reorder_level, product.emergency_order_level)

        facility = SupplyPoint.objects.filter(type__code=SupplyPointCodes.FACILITY)[0]
        for product in Product.objects.filter(type__base_level=BaseLevel.FACILITY):
            ps = ProductStock.objects.create(supply_point=facility, product=product)
            self.assertEqual(ps.emergency_reorder_level, product.emergency_order_level)


class TestAddRemoveProducts(MalawiTestBase):

    def assertProductStock(self, supply_point, product_code, is_active):
        try:
            ps = ProductStock.objects.get(supply_point=supply_point, product__sms_code=product_code)
        except ProductStock.DoesNotExist:
            ps = None

        self.assertTrue(ps is not None)
        self.assertEqual(ps.is_active, is_active)

    def testWrongProductBaseLevel(self):
        hsa = create_hsa(self, "+16175551234", "bob")
        epi_product = Product.objects.filter(type__base_level=BaseLevel.FACILITY)[0]

        a = """
           +16175551234 > add %(product_code)s
           +16175551234 < %(response)s
           +16175551234 > remove %(product_code)s
           +16175551234 < %(response)s
        """ % {
            "product_code": epi_product.sms_code,
            "response": Messages.UNKNOWN_CODE % {"product": epi_product.sms_code}
        }
        self.runScript(a)

    def testAddRemoveProduct(self):

        a = """
           +16175551234 > add zi
           +16175551234 < Sorry, you have to be registered with the system to do that. For help, please contact your supervisor
        """
        self.runScript(a)

        hsa = create_hsa(self, "+16175551234", "stella")

        self.assertFalse(hsa.supply_point.supplies_product(Product.objects.get(sms_code="zi")))
        self.assertFalse(Product.objects.get(sms_code="zi") in hsa.commodities.all())

        a = """
           +16175551234 > add quux
           +16175551234 < Sorry, no product matches code quux.  Nothing done.
           +16175551234 > add zi
           +16175551234 < Thank you, you now supply: zi
        """
        self.runScript(a)

        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="zi")))
        self.assertTrue(Product.objects.get(sms_code="zi") in hsa.commodities.all())
        self.assertProductStock(hsa.supply_point, "zi", True)

        b = """
           +16175551234 > add zi de dm
           +16175551234 < Thank you, you now supply: de dm zi
        """
        self.runScript(b)


        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="zi")))
        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="de")))
        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="dm")))
        self.assertFalse(hsa.supply_point.supplies_product(Product.objects.get(sms_code="cm")))
        self.assertProductStock(hsa.supply_point, "zi", True)
        self.assertProductStock(hsa.supply_point, "de", True)
        self.assertProductStock(hsa.supply_point, "dm", True)

        c = """
           +16175551234 > remove cm
           +16175551234 < Done. You now supply: de dm zi
           +16175551234 > remove de
           +16175551234 < Done. You now supply: dm zi
           """
        self.runScript(c)

        self.assertFalse(Product.objects.get(sms_code="cm") in hsa.commodities.all())
        self.assertFalse(Product.objects.get(sms_code="de") in hsa.commodities.all())

        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="zi")))
        self.assertFalse(hsa.supply_point.supplies_product(Product.objects.get(sms_code="de")))
        self.assertTrue(hsa.supply_point.supplies_product(Product.objects.get(sms_code="dm")))
        self.assertFalse(hsa.supply_point.supplies_product(Product.objects.get(sms_code="cm")))
        self.assertProductStock(hsa.supply_point, "de", False)
        self.assertProductStock(hsa.supply_point, "dm", True)
        self.assertProductStock(hsa.supply_point, "zi", True)
