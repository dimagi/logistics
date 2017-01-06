from __future__ import absolute_import
from logistics.models import ProductStock, SupplyPoint, ProductReport, Product
from logistics_project.apps.malawi.tests.util import create_hsa
from logistics_project.apps.malawi.tests.base import MalawiTestBase
from rapidsms.contrib.messagelog.models import Message
from static.malawi import config


class MalawiTestReceipts(MalawiTestBase):

    def setUp(self):
        super(MalawiTestReceipts, self).setUp()
        ProductReport.objects.all().delete()

    def testReceiptsNormal(self):
        create_hsa(self, "16175551000", "wendy", products="co la lb zi")
        c = """
           16175551000 > rec zi 100 la 200
           16175551000 < Thank you, you reported receipts for zi la.
        """
        self.runScript(c)
        self.assertEqual(2, ProductReport.objects.count())
        zi = ProductStock.objects.get(product__sms_code="zi", supply_point=SupplyPoint.objects.get(code="261601"))
        la = ProductStock.objects.get(product__sms_code="la", supply_point=SupplyPoint.objects.get(code="261601"))
        self.assertEqual(100, zi.quantity)
        self.assertEqual(200, la.quantity)
        c = """
           16175551000 > rec zi 100 la 100
           16175551000 < Thank you, you reported receipts for zi la.
        """
        self.runScript(c)
        self.assertEqual(4, ProductReport.objects.count())
        zi = ProductStock.objects.get(product__sms_code="zi", supply_point=SupplyPoint.objects.get(code="261601"))
        la = ProductStock.objects.get(product__sms_code="la", supply_point=SupplyPoint.objects.get(code="261601"))
        self.assertEqual(200, zi.quantity)
        self.assertEqual(300, la.quantity)

    def testReceiptsIgnoreDupes(self):
        create_hsa(self, "16175551000", "wendy", products="co la lb zi")
        c = """
           16175551000 > rec zi 100 la 200
           16175551000 < Thank you, you reported receipts for zi la.
        """
        self.runScript(c)
        outbound_message_count = Message.objects.filter(direction='O').count()
        c = """
           16175551000 > rec zi 100 la 200
        """
        self.runScript(c)
        # ensure no new outbound message was sent
        self.assertEqual(outbound_message_count, Message.objects.filter(direction='O').count())
        self.assertEqual(2, ProductReport.objects.count())
        zi = ProductStock.objects.get(product__sms_code="zi", supply_point=SupplyPoint.objects.get(code="261601"))
        la = ProductStock.objects.get(product__sms_code="la", supply_point=SupplyPoint.objects.get(code="261601"))
        self.assertEqual(100, zi.quantity)
        self.assertEqual(200, la.quantity)

    def testFacilityLevelProduct(self):
        create_hsa(self, "16175551000", "wendy", products="co la lb zi")
        product_code = Product.objects.filter(type__base_level=config.BaseLevel.FACILITY)[0].sms_code
        self.runScript("""
            16175551000 > rec %(product_code)s 20
            16175551000 < %(error)s
        """ % {
            "product_code": product_code,
            "error": config.Messages.INVALID_PRODUCTS % {"product_codes": product_code},
        })

    def testNonExistentProduct(self):
        create_hsa(self, "16175551000", "wendy", products="co la lb zi")
        self.runScript("""
            16175551000 > rec uvw 10 xyz 20
            16175551000 < %(error)s
        """ % {
            "error": config.Messages.INVALID_PRODUCTS % {"product_codes": "uvw,xyz"},
        })
