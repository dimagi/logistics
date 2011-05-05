from __future__ import absolute_import
from logistics.apps.logistics.models import ProductStock, \
    StockRequest, SupplyPoint, StockRequestStatus
from logistics.apps.logistics.util import config
from logistics.apps.malawi.tests.util import create_hsa, create_manager
from logistics.apps.malawi.tests.base import MalawiTestBase

class TestReport(MalawiTestBase):
    
    def testBadRoles(self):
        create_hsa(self, "16175551000", "joe")
        create_manager(self, "16175551234", "charles", role="hsa")
        a = """
           16175551234 > report 261601 soh zi 40 la 200 
           16175551234 < %(bad_role)s
        """ % {"bad_role": config.Messages.UNSUPPORTED_OPERATION}
               
        self.runScript(a)
    
    def testBadHsaId(self):
        create_manager(self, "16175551234", "charles", role="ic")
        a = """
           16175551234 > report 261601 soh zi 40 la 200 
           16175551234 < %(bad_hsa)s
        """ % {"bad_hsa": config.Messages.UNKNOWN_HSA % {"hsa_id": 261601}}
        
        self.runScript(a)
    
    def testSohAndReceiptReporting(self):
        create_manager(self, "16175551234", "charles", role="ic")
        create_hsa(self, "16175551000", "joe")
        a = """
           16175551234 > report 261601 soh zi 40 la 200 
           16175551234 < joe needs the following products: zi 360, la 520. Type 'report 261601 rec [prod code] [amount]' to report receipts for the HSA.
        """ 
        self.runScript(a)
        hsa_sp = SupplyPoint.objects.get(code=261601)
        self.assertEqual(40, ProductStock.objects.get(supply_point=hsa_sp, product__sms_code="zi").quantity)
        self.assertEqual(200, ProductStock.objects.get(supply_point=hsa_sp, product__sms_code="la").quantity)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(hsa_sp, req.supply_point)
            self.assertEqual(StockRequestStatus.REQUESTED, req.status)
            self.assertTrue(req.is_pending())
        b = """
           16175551234 > report 261601 rec zi 360 la 520
           16175551234 < Thank you charles. You reported the following receipts for joe: zi la
        """ 
        self.runScript(b)
        self.assertEqual(400, ProductStock.objects.get(supply_point=hsa_sp, product__sms_code="zi").quantity)
        self.assertEqual(720, ProductStock.objects.get(supply_point=hsa_sp, product__sms_code="la").quantity)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(hsa_sp, req.supply_point)
            self.assertEqual(StockRequestStatus.RECEIVED, req.status)
            self.assertFalse(req.is_pending())
        
    def testReceiptReporting(self):
        create_manager(self, "16175551234", "charles", role="ic")
        create_hsa(self, "16175551000", "joe")
        a = """
           16175551234 > report 261601 rec zi 100 la 400 
           16175551234 < Thank you charles. You reported the following receipts for joe: zi la
        """ 
        self.runScript(a)
        hsa_sp = SupplyPoint.objects.get(code=261601)
        self.assertEqual(100, ProductStock.objects.get(supply_point=hsa_sp, product__sms_code="zi").quantity)
        self.assertEqual(400, ProductStock.objects.get(supply_point=hsa_sp, product__sms_code="la").quantity)
        