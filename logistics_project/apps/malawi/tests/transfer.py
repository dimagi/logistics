from __future__ import absolute_import
from logistics.models import Product, ProductStock, \
    SupplyPoint, StockTransfer, StockTransferStatus
from logistics.util import config
from logistics_project.apps.malawi.tests.util import create_manager, create_hsa
from logistics_project.apps.malawi.tests.base import MalawiTestBase


class TestTransfer(MalawiTestBase):
    
    def testBadRoles(self):
        create_manager(self, "+16175551234", "cindy", "dp", supply_point_code="26")
        create_hsa(self, "+16175551235", "alex", products="zi")
        a = """
           +16175551234 > give 261601 zi 20 
           +16175551234 < %(bad_role)s
           +16175551235 > give 2616 zi 20
           +16175551235 < Cannot find hsa with id 2616. Please double check the id and try again.
        """ % {"bad_role": config.Messages.UNSUPPORTED_OPERATION}
        self.runScript(a)
        
    def testBasicTransfer(self):
        create_hsa(self, "+16175551000", "wendy", products="zi")
        create_hsa(self, "+16175551001", "steve", id="2", products="zi")
        a = """
           +16175551000 > soh zi 100
           +16175551000 < %(no_super)s
           +16175551001 > soh zi 10
           +16175551001 < %(no_super)s
        """ % {"no_super": config.Messages.NO_IN_CHARGE % {"supply_point": "Ntaja"}}
        self.runScript(a)
        stock_from = ProductStock.objects.get(supply_point=SupplyPoint.objects.get(code="261601"), 
                                              product=Product.by_code("zi"))
        stock_to = ProductStock.objects.get(supply_point=SupplyPoint.objects.get(code="261602"), 
                                            product=Product.by_code("zi"))
        self.assertEqual(100, stock_from.quantity)
        self.assertEqual(10, stock_to.quantity)
        
        b = """
           +16175551000 > give 261602 zi 20
           +16175551000 < %(confirm)s
           +16175551001 < Confirm receipt of zi 20 from wendy? Please respond 'confirm'
        """ % {"confirm": config.Messages.TRANSFER_RESPONSE % \
                    {"giver": "wendy", "receiver": "steve", 
                     "reporter": "wendy", "products": "zi 20"}}
        self.runScript(b)
        self.assertEqual(80, ProductStock.objects.get(pk=stock_from.pk).quantity)
        self.assertEqual(10, ProductStock.objects.get(pk=stock_to.pk).quantity)
        [st] = StockTransfer.objects.all()
        self.assertTrue(st.is_pending())
        self.assertEqual(20, st.amount)
        self.assertEqual(Product.by_code("zi"), st.product)
        self.assertEqual(SupplyPoint.objects.get(code="261601"), st.giver)
        self.assertEqual(SupplyPoint.objects.get(code="261602"), st.receiver)
        
        c = """
           +16175551001 > confirm
           +16175551001 < Thank you steve. You have confirmed receipt of the following products: zi 20
        """
        self.runScript(c)
        self.assertEqual(80, ProductStock.objects.get(pk=stock_from.pk).quantity)
        self.assertEqual(30, ProductStock.objects.get(pk=stock_to.pk).quantity)
        [st] = StockTransfer.objects.all()
        self.assertTrue(st.is_closed())
        
        
    def testTransferFromReceipt(self):
        create_hsa(self, "+16175551000", "wendy")
        create_hsa(self, "+16175551001", "steve", id="2")
        a = """
           +16175551000 > rec zi 100 la 250 from 261602
           +16175551000 < Thank you, you reported receipts for la zi from 261602.
        """
        self.runScript(a)
        self.assertEqual(2, StockTransfer.objects.count())
        self.assertEqual(100, StockTransfer.objects.get(product__sms_code="zi").amount)
        self.assertEqual(250, StockTransfer.objects.get(product__sms_code="la").amount)
        for transfer in StockTransfer.objects.all():
            self.assertEqual(SupplyPoint.objects.get(code="261602"), transfer.giver)
            self.assertEqual("", transfer.giver_unknown)
            self.assertEqual(SupplyPoint.objects.get(code="261601"), transfer.receiver)
            self.assertEqual(StockTransferStatus.CONFIRMED, transfer.status)
            self.assertEqual(None, transfer.initiated_on)
            
    def testTransferFromReceiptNoSupplyPoint(self):
        create_hsa(self, "+16175551000", "wendy")
        a = """
           +16175551000 > rec zi 100 la 250 from someone random
           +16175551000 < Thank you, you reported receipts for la zi from someone random.
        """
        self.runScript(a)
        self.assertEqual(2, StockTransfer.objects.count())
        self.assertEqual(100, StockTransfer.objects.get(product__sms_code="zi").amount)
        self.assertEqual(250, StockTransfer.objects.get(product__sms_code="la").amount)
        for transfer in StockTransfer.objects.all():
            self.assertEqual(None, transfer.giver)
            self.assertEqual("someone random", transfer.giver_unknown)
            self.assertEqual(SupplyPoint.objects.get(code="261601"), transfer.receiver)
            self.assertEqual(StockTransferStatus.CONFIRMED, transfer.status)
            self.assertEqual(None, transfer.initiated_on)

    def testFacilityLevelProduct(self):
        create_hsa(self, "+16175551000", "wendy", products="zi")
        create_hsa(self, "+16175551001", "steve", id="2", products="zi")
        product_code = Product.objects.filter(type__base_level=config.BaseLevel.FACILITY)[0].sms_code
        self.runScript("""
            +16175551000 > give 261602 %(product_code)s 20
            +16175551000 < %(error)s
        """ % {
            "product_code": product_code,
            "error": config.Messages.INVALID_PRODUCTS % {"product_codes": product_code},
        })

    def testNonExistentProduct(self):
        create_hsa(self, "+16175551000", "wendy", products="zi")
        create_hsa(self, "+16175551001", "steve", id="2", products="zi")
        self.runScript("""
            +16175551000 > give 261602 uvw 10 xyz 20
            +16175551000 < %(error)s
        """ % {
            "error": config.Messages.INVALID_PRODUCTS % {"product_codes": "uvw,xyz"},
        })
