from __future__ import absolute_import
from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
from logistics.apps.logistics.models import Product, ProductStock, \
    StockRequest, SupplyPoint, StockRequestStatus, StockTransfer,\
    StockTransferStatus
from logistics.apps.malawi import app as malawi_app
from rapidsms.models import Contact
from logistics.apps.malawi.const import Messages
from logistics.apps.malawi.tests.util import create_manager, create_hsa

class TestTransfer(TestScript):
    apps = ([malawi_app.App])
    fixtures = ["malawi_products.json"]
    
    def testBadRoles(self):
        create_manager(self, "16175551234", "cindy")
        create_hsa(self, "16175551235", "alex")
        a = """
           16175551234 > give 261601 zi 20 
           16175551234 < %(bad_role)s
           16175551235 > give 2616 zi 20
           16175551235 < Cannot find hsa with id 2616. Please double check the id and try again.
        """ % {"bad_role": Messages.UNSUPPORTED_OPERATION}
        self.runScript(a)
        
    def testBasicTransfer(self):
        create_hsa(self, "16175551000", "wendy")
        create_hsa(self, "16175551001", "steve", id="2")
        a = """
           16175551000 > soh zi 100
           16175551000 < There is no in-charge registered for Ntaja. Please contact your supervisor to resolve this.
           16175551001 > soh zi 10
           16175551001 < There is no in-charge registered for Ntaja. Please contact your supervisor to resolve this.
           
        """
        self.runScript(a)
        stock_from = ProductStock.objects.get(supply_point=SupplyPoint.objects.get(code="261601"), 
                                              product=Product.by_code("zi"))
        stock_to = ProductStock.objects.get(supply_point=SupplyPoint.objects.get(code="261602"), 
                                            product=Product.by_code("zi"))
        self.assertEqual(100, stock_from.quantity)
        self.assertEqual(10, stock_to.quantity)
        
        b = """
           16175551000 > give 261602 zi 20
           16175551000 < Thank you wendy. You have transfered steve the following products: zi 20
           16175551001 < Confirm receipt of zi 20 from wendy? Please respond 'confirm'
        """
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
           16175551001 > confirm
           16175551001 < Thank you steve. You have confirmed receipt of the following products: zi 20
        """
        self.runScript(c)
        self.assertEqual(80, ProductStock.objects.get(pk=stock_from.pk).quantity)
        self.assertEqual(30, ProductStock.objects.get(pk=stock_to.pk).quantity)
        [st] = StockTransfer.objects.all()
        self.assertTrue(st.is_closed())
        
        
    def testTransferFromReceipt(self):
        create_hsa(self, "16175551000", "wendy")
        create_hsa(self, "16175551001", "steve", id="2")
        a = """
           16175551000 > rec zi 100 la 250 from 261602
           16175551000 < Thank you, you reported receipts for zi la.
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
        create_hsa(self, "16175551000", "wendy")
        a = """
           16175551000 > rec zi 100 la 250 from someone random
           16175551000 < Thank you, you reported receipts for zi la.
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
            
        