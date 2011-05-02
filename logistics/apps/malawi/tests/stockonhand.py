from __future__ import absolute_import
from rapidsms.tests.scripted import TestScript
from logistics.apps.logistics.models import StockRequest, SupplyPoint, StockRequestStatus ,\
    ProductStock
from logistics.apps.malawi import app as malawi_app
from rapidsms.models import Contact
from logistics.apps.malawi.tests.util import create_hsa, create_manager,\
    report_stock
from logistics.apps.malawi.const import Roles, Messages

class TestStockOnHandMalawi(TestScript):
    
    def testNoInCharge(self):
        create_hsa(self, "16175551234", "stella")
        a = """
           16175551234 > soh zi 10
           16175551234 < %(no_super)s
           """ % {"no_super": Messages.NO_IN_CHARGE % {"supply_point": "Ntaja"}}
        self.runScript(a)
        
    def testBasicSupplyFlow(self):
        hsa, ic = self._setup_users()[0:2]
        report_stock(self, hsa, "zi 10 la 15", ic, "zi 390, la 705")
        
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
           16175551001 < %(confirm)s
           16175551000 < %(hsa_notice)s
        """ % {"confirm": Messages.APPROVAL_RESPONSE % \
                    {"hsa": "wendy", "products": "zi, la"},
               "hsa_notice": Messages.APPROVAL_NOTICE % \
                    {"hsa": "wendy", "products": "zi, la"}}
        

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
        hsa, ic = self._setup_users()[0:2]
        
        report_stock(self, hsa, "zi 10 la 15", ic, "zi 390, la 705")
        
        a = """
           16175551001 > os 261601
           16175551001 < %(confirm)s
           16175551002 < %(district)s
           16175551003 < %(district)s
           16175551000 < %(hsa_notice)s
        """ % {"confirm": Messages.STOCKOUT_RESPONSE %\
                    {"reporter": "sally", "products": "zi, la"},
               "district": Messages.SUPERVISOR_STOCKOUT_NOTIFICATION  % \
                    {"contact": "sally", "supply_point": "Ntaja", "products": "zi, la"},
               "hsa_notice": Messages.STOCKOUT_NOTICE % {"hsa": "wendy"}}
                    
                    
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
        
    
    def testEmergencyStockOnHand(self):
        self._setup_users()
        a = """
           16175551000 > eo zi 10 la 500
           16175551000 < %(confirm)s
           16175551001 < wendy needs emergency products: zi 390, and additionally: la 220. Respond 'ready 261601' or 'os 261601'
        """ % {"confirm": Messages.SOH_ORDER_CONFIRM % {"contact": "wendy"}}
                    
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
    
    def testEmergencyStockOut(self):
        self.testEmergencyStockOnHand()
        # the difference here is that only emergency products are
        # reported/escalated 
        a = """
           16175551001 > os 261601
           16175551001 < %(confirm)s
           16175551002 < %(district)s
           16175551003 < %(district)s
           16175551000 < %(hsa_notice)s
        """ % {"confirm": Messages.STOCKOUT_RESPONSE %\
                    {"reporter": "sally", "products": "zi"},
               "district": Messages.SUPERVISOR_STOCKOUT_NOTIFICATION  % \
                    {"contact": "sally", "supply_point": "Ntaja", "products": "zi"},
               "hsa_notice": Messages.STOCKOUT_NOTICE % {"hsa": "wendy"}}
        self.runScript(a)
        
    def testEmergencyOrderNoProductsInEmergency(self):
        self._setup_users()
        a = """
           16175551000 > eo zi 400 la 500
           16175551000 < %(confirm)s
           16175551001 < wendy needs emergency products: none, and additionally: la 220. Respond 'ready 261601' or 'os 261601'
        """ % {"confirm": Messages.SOH_ORDER_CONFIRM % {"contact": "wendy"}}
                    
        self.runScript(a)
        
    def testEmergencyOrderNoProductsNotInEmergency(self):
        self._setup_users()
        a = """
           16175551000 > eo zi 0 la 0
           16175551000 < %(confirm)s
           16175551001 < wendy needs emergency products: zi 400, la 720. Respond 'ready 261601' or 'os 261601'
        """ % {"confirm": Messages.SOH_ORDER_CONFIRM % {"contact": "wendy"}}
                    
        self.runScript(a)
        
        
    def _setup_users(self):
        hsa = create_hsa(self, "16175551000", "wendy")
        ic = create_manager(self, "16175551001", "sally")
        im = create_manager(self, "16175551002", "peter", Roles.IMCI_COORDINATOR, "26")
        dp = create_manager(self, "16175551003", "ruth", Roles.DISTRICT_PHARMACIST, "26")
        return (hsa, ic, im, dp) 
        