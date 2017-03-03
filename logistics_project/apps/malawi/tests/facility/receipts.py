from __future__ import absolute_import
from logistics.models import ProductStock, SupplyPoint, ProductReport, Product
from logistics_project.apps.malawi.tests.facility.base import MalawiFacilityLevelTestBase
from rapidsms.contrib.messagelog.models import Message
from static.malawi import config


class MalawiTestFacilityReceipts(MalawiFacilityLevelTestBase):

    def setUp(self):
        super(MalawiTestFacilityReceipts, self).setUp()
        ProductReport.objects.all().delete()

    def testReceiptsNormal(self):
        self._setup_users()
        self.runScript("""
           +16175551000 > rec bc 100 sa 2
           +16175551000 < %(response)s
        """ % {
            "response": config.Messages.RECEIPT_CONFIRM % {"products": "sa bc"}
        })
        self.assertEqual(2, ProductReport.objects.count())
        bc = ProductStock.objects.get(product__sms_code="bc", supply_point__code="2616")
        sa = ProductStock.objects.get(product__sms_code="sa", supply_point__code="2616")
        self.assertEqual(100, bc.quantity)
        self.assertEqual(2, sa.quantity)
        self.runScript("""
           +16175551000 > rec bc 100 sa 3
           +16175551000 < %(response)s
        """ % {
            "response": config.Messages.RECEIPT_CONFIRM % {"products": "sa bc"}
        })
        self.assertEqual(4, ProductReport.objects.count())
        bc = ProductStock.objects.get(product__sms_code="bc", supply_point__code="2616")
        sa = ProductStock.objects.get(product__sms_code="sa", supply_point__code="2616")
        self.assertEqual(200, bc.quantity)
        self.assertEqual(5, sa.quantity)

    def testReceiptsIgnoreDupes(self):
        self._setup_users()
        self.runScript("""
           +16175551000 > rec bc 100 sa 2
           +16175551000 < %(response)s
        """ % {
            "response": config.Messages.RECEIPT_CONFIRM % {"products": "sa bc"}
        })
        self.assertEqual(2, ProductReport.objects.count())
        bc = ProductStock.objects.get(product__sms_code="bc", supply_point__code="2616")
        sa = ProductStock.objects.get(product__sms_code="sa", supply_point__code="2616")
        self.assertEqual(100, bc.quantity)
        self.assertEqual(2, sa.quantity)
        outbound_message_count = Message.objects.filter(direction='O').count()

        self.runScript("+16175551000 > rec bc 100 sa 2")
        # ensure no new outbound message was sent
        self.assertEqual(outbound_message_count, Message.objects.filter(direction='O').count())
        self.assertEqual(2, ProductReport.objects.count())
        bc = ProductStock.objects.get(product__sms_code="bc", supply_point__code="2616")
        sa = ProductStock.objects.get(product__sms_code="sa", supply_point__code="2616")
        self.assertEqual(100, bc.quantity)
        self.assertEqual(2, sa.quantity)

    def testHSALevelProduct(self):
        self._setup_users()
        product_code = Product.objects.filter(type__base_level=config.BaseLevel.HSA)[0].sms_code
        self.runScript("""
            +16175551000 > rec %(product_code)s 20
            +16175551000 < %(error)s
        """ % {
            "product_code": product_code,
            "error": config.Messages.INVALID_PRODUCTS % {"product_codes": product_code},
        })

    def testNonExistentProduct(self):
        self._setup_users()
        self.runScript("""
            +16175551000 > rec uvw 10 xyz 20
            +16175551000 < %(error)s
        """ % {
            "error": config.Messages.INVALID_PRODUCTS % {"product_codes": "uvw,xyz"},
        })
