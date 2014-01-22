from __future__ import absolute_import
from logistics.models import ProductStock, SupplyPoint, ProductReport
from logistics_project.apps.malawi.tests.util import create_hsa
from logistics_project.apps.malawi.tests.base import MalawiTestBase


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
        c = """
           16175551000 > rec zi 100 la 200
           16175551000 < Your receipt has already been received. To report a new receipt please change product order or amounts.
        """
        self.runScript(c)
        self.assertEqual(2, ProductReport.objects.count())
        zi = ProductStock.objects.get(product__sms_code="zi", supply_point=SupplyPoint.objects.get(code="261601"))
        la = ProductStock.objects.get(product__sms_code="la", supply_point=SupplyPoint.objects.get(code="261601"))
        self.assertEqual(100, zi.quantity)
        self.assertEqual(200, la.quantity)
