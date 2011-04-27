from __future__ import absolute_import
from rapidsms.tests.scripted import TestScript
from logistics.apps.logistics.models import StockRequest, SupplyPoint, StockRequestStatus ,\
    ProductStock
from logistics.apps.malawi import app as malawi_app
from rapidsms.models import Contact

class TestStockOnHandMalawi(TestScript):
    apps = ([malawi_app.App])
    fixtures = ["malawi_products.json"]
    
    def testNoInCharge(self):
        
        a = """
        
           16175551234 > register stella 1 2616
           16175551234 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Ntaja
           16175551234 > soh zi 10
           16175551234 < There is no in-charge registered for Ntaja. Please contact your supervisor to resolve this.
           """
        self.runScript(a)
        
    def testBasicSupplyFlow(self):
        self._setup_users()
        a = """
           16175551000 > soh zi 10 la 15
           16175551000 < Thank you wendy. The health center in charge has been notified and you will receive an alert when supplies are ready.
           16175551001 < wendy needs the following supplies: zi 390, la 705. Respond 'ready 261601' when supplies are ready
        """
        self.runScript(a)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(req.supply_point, SupplyPoint.objects.get(code="261601"))
            self.assertEqual(StockRequestStatus.REQUESTED, req.status)
            self.assertTrue(req.is_pending())
            self.assertFalse(req.is_emergency)
        zi = ProductStock.objects.get(product__sms_code="zi", supply_point=SupplyPoint.objects.get(code="261601"))
        la = ProductStock.objects.get(product__sms_code="la", supply_point=SupplyPoint.objects.get(code="261601"))
        self.assertEqual(zi.quantity, 10)
        self.assertEqual(la.quantity, 15)
        b = """
           16175551001 > ready 261601
           16175551001 < Thank you for confirming order for wendy. You approved: zi 390, la 705
           16175551000 < Dear wendy, your pending order has been approved. The following supplies are ready: zi 390, la 705
        """
        self.runScript(b)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(StockRequestStatus.APPROVED, req.status)
            self.assertTrue(req.is_pending())
            self.assertEqual(Contact.objects.get(name="sally"), req.responded_by)
            self.assertEqual(req.amount_requested, req.amount_approved)
            self.assertTrue(req.responded_on > req.requested_on)
                    
        # stocks shouldn't get updated
        self.assertEqual(ProductStock.objects.get(pk=zi.pk).quantity, 10)
        self.assertEqual(ProductStock.objects.get(pk=la.pk).quantity, 15)
        
        c = """
           16175551000 > rec zi 390 la 705
           16175551000 < Thank you, you reported receipts for zi la.
        """
        self.runScript(c)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(StockRequestStatus.RECEIVED, req.status)
            self.assertFalse(req.is_pending())
            self.assertEqual(Contact.objects.get(name="wendy"), req.received_by)
            self.assertEqual(req.amount_received, req.amount_requested)
            self.assertTrue(req.received_on > req.responded_on > req.requested_on)
        
        # stocks should now be updated
        self.assertEqual(ProductStock.objects.get(pk=zi.pk).quantity, 400)
        self.assertEqual(ProductStock.objects.get(pk=la.pk).quantity, 720)
        
    def testStockoutSupplyFlow(self):
        self._setup_users()
        a = """
           16175551000 > soh zi 10 la 15
           16175551000 < Thank you wendy. The health center in charge has been notified and you will receive an alert when supplies are ready.
           16175551001 < wendy needs the following supplies: zi 390, la 705. Respond 'ready 261601' when supplies are ready
           16175551001 > os 261601
           16175551001 < Thank you sally. You have reported stockouts for the following products: zi, la. The district office has been notified.
           16175551000 < Dear wendy, your pending order is stocked out at the facility. Please work with the in-charge to resolve this issue in a timely manner.
        """
        self.runScript(a)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(req.supply_point, SupplyPoint.objects.get(code="261601"))
            self.assertEqual(StockRequestStatus.STOCKED_OUT, req.status)
            self.assertTrue(req.is_pending())
        zi = ProductStock.objects.get(product__sms_code="zi", supply_point=SupplyPoint.objects.get(code="261601"))
        la = ProductStock.objects.get(product__sms_code="la", supply_point=SupplyPoint.objects.get(code="261601"))
        self.assertEqual(zi.quantity, 10)
        self.assertEqual(la.quantity, 15)
        
    def testPartialFillSupplyFlow(self):
        self._setup_users()
        a = """
           16175551000 > soh zi 10 la 15
           16175551000 < Thank you wendy. The health center in charge has been notified and you will receive an alert when supplies are ready.
           16175551001 < wendy needs the following supplies: zi 390, la 705. Respond 'ready 261601' when supplies are ready
           16175551001 > partial 261601
           16175551001 < Thank you for partially confirming order for wendy. You approved some of: zi, la
           16175551000 < Dear wendy, your pending is now ready to be partially filled. Not all products were available but some are ready.
        """
        self.runScript(a)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(req.supply_point, SupplyPoint.objects.get(code="261601"))
            self.assertEqual(StockRequestStatus.PARTIALLY_STOCKED, req.status)
            self.assertTrue(req.is_pending())
        zi = ProductStock.objects.get(product__sms_code="zi", supply_point=SupplyPoint.objects.get(code="261601"))
        la = ProductStock.objects.get(product__sms_code="la", supply_point=SupplyPoint.objects.get(code="261601"))
        self.assertEqual(zi.quantity, 10)
        self.assertEqual(la.quantity, 15)
        
    def testEmergencyStockOnHand(self):
        self._setup_users()
        a = """
           16175551000 > eo zi 10 la 500
           16175551000 < Thank you wendy. The health center in charge has been notified and you will receive an alert when supplies are ready.
           16175551001 < wendy needs emergency products: zi 390, and additionally: la 220. Respond 'ready 261601' or 'os 261601'
        """
        self.runScript(a)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(req.supply_point, SupplyPoint.objects.get(code="261601"))
            self.assertEqual(StockRequestStatus.REQUESTED, req.status)
            self.assertTrue(req.is_pending())
            if req.product.sms_code == "zi":
                self.assertTrue(req.is_emergency)
            else:
                self.assertEqual("la", req.product.sms_code)
                self.assertFalse(req.is_emergency)
        zi = ProductStock.objects.get(product__sms_code="zi", supply_point=SupplyPoint.objects.get(code="261601"))
        la = ProductStock.objects.get(product__sms_code="la", supply_point=SupplyPoint.objects.get(code="261601"))
        self.assertEqual(zi.quantity, 10)
        self.assertEqual(la.quantity, 500)
        
        
    def _setup_users(self):
        a = """
           16175551000 > register wendy 1 2616
           16175551000 < Congratulations wendy, you have successfully been registered for the Early Warning System. Your facility is Ntaja
           16175551001 > manage sally ic 2616
           16175551001 < Congratulations sally, you have successfully been registered for the Early Warning System. Your facility is Ntaja
        """
        self.runScript(a)
