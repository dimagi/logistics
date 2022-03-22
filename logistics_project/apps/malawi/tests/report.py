from __future__ import absolute_import
from logistics.models import ProductStock, \
    StockRequest, SupplyPoint, StockRequestStatus, StockTransfer, Product
from logistics.util import config
from logistics_project.apps.malawi.tests.util import create_hsa, create_manager
from logistics_project.apps.malawi.tests.base import MalawiTestBase

class TestReport(MalawiTestBase):
    
    def testBadHsaId(self):
        create_manager(self, "+16175551234", "charles", role="ic")
        a = """
           +16175551234 > report 261601 soh zi 40 la 200 
           +16175551234 < %(bad_hsa)s
        """ % {"bad_hsa": config.Messages.UNKNOWN_HSA % {"hsa_id": 261601}}
        
        self.runScript(a)

    def testWrongLevelProduct(self):
        product_code = Product.objects.filter(type__base_level=config.BaseLevel.FACILITY)[0].sms_code
        create_hsa(self, "+16175551000", "giver")
        create_hsa(self, "+16175551001", "receiver", "2")
        create_hsa(self, "+16175551002", "reporter", "3")

        self.runScript(
            """ +16175551002 > report 261601 give 261602 %(product_code)s 20
                +16175551002 < %(response)s
            """ % {
                "product_code": product_code,
                "response": config.Messages.INVALID_PRODUCTS % {"product_codes": product_code},
            }
        )

        self.runScript(
            """ +16175551002 > report 261601 soh %(product_code)s 20
                +16175551002 < %(response)s
            """ % {
                "product_code": product_code,
                "response": config.Messages.INVALID_PRODUCTS % {"product_codes": product_code},
            }
        )

        self.runScript(
            """ +16175551002 > report 261601 eo %(product_code)s 20
                +16175551002 < %(response)s
            """ % {
                "product_code": product_code,
                "response": config.Messages.INVALID_PRODUCTS % {"product_codes": product_code},
            }
        )

        self.runScript(
            """ +16175551002 > report 261601 rec %(product_code)s 20
                +16175551002 < %(response)s
            """ % {
                "product_code": product_code,
                "response": config.Messages.INVALID_PRODUCTS % {"product_codes": product_code},
            }
        )

    def testNonExistentProduct(self):
        create_hsa(self, "+16175551000", "giver")
        create_hsa(self, "+16175551001", "receiver", "2")
        create_hsa(self, "+16175551002", "reporter", "3")

        self.runScript(
            """ +16175551002 > report 261601 give 261602 uvw 10 xyz 20
                +16175551002 < %(response)s
            """ % {
                "response": config.Messages.INVALID_PRODUCTS % {"product_codes": "uvw,xyz"},
            }
        )

        self.runScript(
            """ +16175551002 > report 261601 soh uvw 10 xyz 20
                +16175551002 < %(response)s
            """ % {
                "response": config.Messages.INVALID_PRODUCTS % {"product_codes": "uvw,xyz"},
            }
        )

        self.runScript(
            """ +16175551002 > report 261601 eo uvw 10 xyz 20
                +16175551002 < %(response)s
            """ % {
                "response": config.Messages.INVALID_PRODUCTS % {"product_codes": "uvw,xyz"},
            }
        )

        self.runScript(
            """ +16175551002 > report 261601 rec uvw 10 xyz 20
                +16175551002 < %(response)s
            """ % {
                "response": config.Messages.INVALID_PRODUCTS % {"product_codes": "uvw,xyz"},
            }
        )

    def testSohAndReceiptReporting(self):
        create_manager(self, "+16175551234", "charles", role="ic")
        create_hsa(self, "+16175551000", "joe")
        a = """
           +16175551234 > report 261601 soh zi 40 la 200 
           +16175551234 < joe needs the following products: zi 160, la 160. Type 'report 261601 rec [prod code] [amount]' to report receipts for the HSA.
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
           +16175551234 > report 261601 rec zi 160 la 160
           +16175551234 < Thank you charles. You reported the following receipts for joe: la zi
        """ 
        self.runScript(b)
        self.assertEqual(200, ProductStock.objects.get(supply_point=hsa_sp, product__sms_code="zi").quantity)
        self.assertEqual(360, ProductStock.objects.get(supply_point=hsa_sp, product__sms_code="la").quantity)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(hsa_sp, req.supply_point)
            self.assertEqual(StockRequestStatus.RECEIVED, req.status)
            self.assertFalse(req.is_pending())
        
    def testReceiptReporting(self):
        create_manager(self, "+16175551234", "charles", role="ic")
        create_hsa(self, "+16175551000", "joe")
        a = """
           +16175551234 > report 261601 rec zi 100 la 400 
           +16175551234 < Thank you charles. You reported the following receipts for joe: la zi
        """ 
        self.runScript(a)
        hsa_sp = SupplyPoint.objects.get(code="261601")
        self.assertEqual(100, ProductStock.objects.get(supply_point=hsa_sp, product__sms_code="zi").quantity)
        self.assertEqual(400, ProductStock.objects.get(supply_point=hsa_sp, product__sms_code="la").quantity)
    
    def testReportForAnotherHSA(self):
        create_manager(self, "+16175551234", "charles", role="ic")
        create_hsa(self, "+16175551000", "joe")
        create_hsa(self, "+16175551001", "phoneless", "2")
        a = """
           +16175551000 > report 261602 soh zi 40 la 200 
           +16175551000 < %(response)s
           +16175551234 < %(super)s
        """ % {"response": config.Messages.SOH_HSA_LEVEL_ORDER_CONFIRM % \
               {"contact": "joe", "products": "la zi"},
               "super": config.Messages.SUPERVISOR_HSA_LEVEL_SOH_NOTIFICATION % \
               {"hsa": "phoneless", "products": "la 160, zi 160",
                "hsa_id": "261602"}}
        self.runScript(a)
        hsa_sp = SupplyPoint.objects.get(code="261602")
        self.assertEqual(40, ProductStock.objects.get(supply_point=hsa_sp, product__sms_code="zi").quantity)
        self.assertEqual(200, ProductStock.objects.get(supply_point=hsa_sp, product__sms_code="la").quantity)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(hsa_sp, req.supply_point)
            self.assertEqual(StockRequestStatus.REQUESTED, req.status)
            self.assertTrue(req.is_pending())
            self.assertFalse(req.is_emergency)
        
    def testReportEmergencyForAnotherHSA(self):
        create_manager(self, "+16175551234", "charles", role="ic")
        create_hsa(self, "+16175551000", "joe")
        create_hsa(self, "+16175551001", "phoneless", "2")
        a = """
           +16175551000 > report 261602 eo zi 40 la 200 
           +16175551000 < %(response)s
           +16175551234 < %(super)s
        """ % {"response": config.Messages.HSA_LEVEL_EMERGENCY_SOH % \
               {"products": "la zi"},
               "super": config.Messages.SUPERVISOR_EMERGENCY_SOH_NOTIFICATION % \
               {"supply_point": "phoneless", "emergency_products": "zi 160",
                "normal_products": "la 160",
                "supply_point_code": "261602"}}
        self.runScript(a)
        hsa_sp = SupplyPoint.objects.get(code="261602")
        self.assertEqual(40, ProductStock.objects.get(supply_point=hsa_sp, product__sms_code="zi").quantity)
        self.assertEqual(200, ProductStock.objects.get(supply_point=hsa_sp, product__sms_code="la").quantity)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(hsa_sp, req.supply_point)
            self.assertEqual(StockRequestStatus.REQUESTED, req.status)
            self.assertTrue(req.is_pending())
            if req.is_emergency:
                self.assertTrue(Product.by_code("zi"), req.product)
            else:
                self.assertTrue(Product.by_code("la"), req.product)
        
    def testReportEmergencyTransfers(self):
        create_hsa(self, "+16175551000", "giver")
        create_hsa(self, "+16175551001", "receiver", "2")
        create_hsa(self, "+16175551002", "reporter", "3")
        a = """
           +16175551002 > report 261601 give 261602 zi 20
           +16175551002 < %(response)s
           +16175551001 < %(receive)s
        """ % {"response": config.Messages.TRANSFER_RESPONSE % \
               {"reporter": "reporter", "giver": "giver", 
                "receiver": "receiver", "products": "zi 20"},
               "receive": config.Messages.TRANSFER_CONFIRM % \
               {"products": "zi 20", "giver": "giver"}}
        self.runScript(a)
        [st] = StockTransfer.objects.all()
        self.assertTrue(st.is_pending())
        self.assertEqual(20, st.amount)
        self.assertEqual(Product.by_code("zi"), st.product)
        self.assertEqual(SupplyPoint.objects.get(code="261601"), st.giver)
        self.assertEqual(SupplyPoint.objects.get(code="261602"), st.receiver)
