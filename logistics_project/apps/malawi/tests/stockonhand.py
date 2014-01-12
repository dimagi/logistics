from __future__ import absolute_import
from logistics.models import StockRequest, SupplyPoint, StockRequestStatus, ProductStock
from rapidsms.models import Contact
from logistics_project.apps.malawi.tests.util import create_hsa, create_manager,\
    report_stock
from logistics.util import config
from logistics_project.apps.malawi.tests.base import MalawiTestBase


class TestStockOnHandMalawi(MalawiTestBase):
    
    def testNoInCharge(self):
        create_hsa(self, "16175551234", "stella", products="zi")
        a = """
           16175551234 > soh zi 10
           16175551234 < %(no_super)s
           """ % {"no_super": config.Messages.NO_IN_CHARGE % {"supply_point": "Ntaja"}}
        self.runScript(a)


    def testNoProductsAdded(self):
        hsa = create_hsa(self, "16175551000", "wendy", products="")
        ic = create_manager(self, "16175551001", "sally")
        a = """
           16175551000 > soh zi 10
           16175551000 < %(no_products)s
           """ % {"no_products": config.Messages.NO_PRODUCTS_MANAGED}
        self.runScript(a)

    def testBasicSupplyFlow(self):
        hsa, ic, sh = self._setup_users()[0:3]
        report_stock(self, hsa, "zi 10 la 15", [ic,sh], "zi 190, la 345")
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(req.supply_point, SupplyPoint.objects.get(code="261601"))
            self.assertEqual(StockRequestStatus.REQUESTED, req.status)
            self.assertEqual("", req.response_status)
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
        """ % {"confirm": config.Messages.APPROVAL_RESPONSE % \
                    {"hsa": "wendy"},
               "hsa_notice": config.Messages.APPROVAL_NOTICE % \
                    {"hsa": "wendy"}}


        self.runScript(b)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(StockRequestStatus.APPROVED, req.status)
            self.assertEqual(StockRequestStatus.APPROVED, req.response_status)
            self.assertTrue(req.is_pending())
            self.assertEqual(Contact.objects.get(name="sally"), req.responded_by)
            self.assertEqual(req.amount_requested, req.amount_approved)
            self.assertTrue(req.responded_on >= req.requested_on)

        # stocks shouldn't get updated
        self.assertEqual(ProductStock.objects.get(pk=zi.pk).quantity, 10)
        self.assertEqual(ProductStock.objects.get(pk=la.pk).quantity, 15)

        c = """
           16175551000 > rec zi 190 la 345
           16175551000 < Thank you, you reported receipts for zi la.
        """
        self.runScript(c)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(StockRequestStatus.RECEIVED, req.status)
            self.assertEqual(StockRequestStatus.APPROVED, req.response_status)
            self.assertFalse(req.is_pending())
            self.assertEqual(Contact.objects.get(name="wendy"), req.received_by)
            self.assertEqual(req.amount_received, req.amount_requested)
            self.assertTrue(req.received_on >= req.responded_on >= req.requested_on)

        # stocks should now be updated
        self.assertEqual(ProductStock.objects.get(pk=zi.pk).quantity, 200)
        self.assertEqual(ProductStock.objects.get(pk=la.pk).quantity, 360)

        # Second receipt should increase normally

        c = """
           16175551000 > rec zi 190 la 345
           16175551000 < Thank you, you reported receipts for zi la.
        """
        self.runScript(c)

        self.assertEqual(ProductStock.objects.get(pk=zi.pk).quantity, 390)
        self.assertEqual(ProductStock.objects.get(pk=la.pk).quantity, 705)


    def testReceiptNoRequest(self):
        hsa = self._setup_users()[0]

        c = """
           16175551000 > rec zi 190 la 345
           16175551000 < Thank you, you reported receipts for zi la.
        """
        self.runScript(c)

        self.assertEqual(190, ProductStock.objects.get(supply_point__code="261601", product__sms_code='zi').quantity)
        self.assertEqual(345, ProductStock.objects.get(supply_point__code="261601", product__sms_code='la').quantity)



    def testAppendStockOnHand(self):
        hsa, ic, sh = self._setup_users()[0:3]
        report_stock(self, hsa, "zi 10 la 15", [ic,sh], "zi 190, la 345")
        self.assertEqual(2, StockRequest.objects.count())
        report_stock(self, hsa, "zi 5 lb 20", [ic,sh], "la 345, lb 172, zi 195")
        self.assertEqual(4, StockRequest.objects.count())
        self.assertEqual(3, StockRequest.objects.filter(status=StockRequestStatus.REQUESTED).count())
        self.assertEqual(1, StockRequest.objects.filter(status=StockRequestStatus.CANCELED).count())
        b = """
           16175551001 > ready 261601
           16175551001 < %(confirm)s
           16175551000 < %(hsa_notice)s
        """ % {"confirm": config.Messages.APPROVAL_RESPONSE % \
                    {"hsa": "wendy"},
               "hsa_notice": config.Messages.APPROVAL_NOTICE % \
                    {"hsa": "wendy"}}
        self.runScript(b)
        self.assertEqual(3, StockRequest.objects.filter(status=StockRequestStatus.APPROVED).count())
        self.assertEqual(1, StockRequest.objects.filter(status=StockRequestStatus.CANCELED).count())


    def testSOHBeforeReceipt(self):
        hsa, ic, sh = self._setup_users()[0:3]
        report_stock(self, hsa, "zi 10 la 15", [ic,sh], "zi 190, la 345")
        zi = ProductStock.objects.get(product__sms_code="zi", supply_point=SupplyPoint.objects.get(code="261601"))
        la = ProductStock.objects.get(product__sms_code="la", supply_point=SupplyPoint.objects.get(code="261601"))
        self.assertEqual(2, StockRequest.objects.filter(status=StockRequestStatus.REQUESTED).count())

        b = """
           16175551001 > ready 261601
           16175551001 < %(confirm)s
           16175551000 < %(hsa_notice)s
        """ % {"confirm": config.Messages.APPROVAL_RESPONSE % \
                    {"hsa": "wendy"},
               "hsa_notice": config.Messages.APPROVAL_NOTICE % \
                    {"hsa": "wendy"}}
        self.runScript(b)
        self.assertEqual(2, StockRequest.objects.filter(status=StockRequestStatus.APPROVED).count())

        report_stock(self, hsa, "zi 10 la 15", [ic,sh], "zi 190, la 345")
        self.assertEqual(2, StockRequest.objects.filter(status=StockRequestStatus.REQUESTED).count())

        c = """
           16175551000 > rec zi 190 la 345
           16175551000 < Thank you, you reported receipts for zi la.
        """
        self.runScript(c)
        self.assertEqual(200, ProductStock.objects.get(pk=zi.pk).quantity)
        self.assertEqual(360, ProductStock.objects.get(pk=la.pk).quantity)
        self.assertEqual(2, StockRequest.objects.filter(status=StockRequestStatus.RECEIVED).count())



    def testNothingToFill(self):
        self._setup_users()
        a = """
            16175551000 > soh zi 600 la 1000
            16175551000 < %(response)s
            16175551001 < %(super)s
        """ % {"response": config.Messages.SOH_ORDER_CONFIRM_NOTHING_TO_DO % \
               {"contact": "wendy", "products": "zi la"},
               "super": config.Messages.SUPERVISOR_SOH_NOTIFICATION_NOTHING_TO_DO % \
               {"hsa": "wendy"}}
        self.runScript(a)
        self.assertEqual(0, StockRequest.objects.count())

    def testBadSubmissions(self):
        return True
        hsa = create_hsa(self, "16175551000", "wendy")
        a = """
            16175551000 > soh zi
            16175551000 < %(no_number)s
            16175551000 > soh 1
            16175551000 < %(no_code)s
        """ % {'no_number': config.Messages.NO_QUANTITY_ERROR,
               'no_code': config.Messages.NO_CODE_ERROR}
        self.runScript(a)
        self.assertEqual(0, StockRequest.objects.count())


    def testStockoutSupplyFlow(self):
        hsa, ic = self._setup_users()[0:2]

        report_stock(self, hsa, "zi 10 la 15", [ic], "zi 190, la 345")

        a = """
           16175551001 > os 261601
           16175551000 < %(hsa_notice)s
           16175551003 < %(district)s
           16175551002 < %(district)s
           16175551001 < %(confirm)s
        """ % {"confirm": config.Messages.HF_UNABLE_RESTOCK_EO %\
                    {"reporter": "sally", "products": "zi, la"},
               "hsa_notice": config.Messages.HSA_UNABLE_RESTOCK_ANYTHING % {"hsa": "wendy"},
               "district": config.Messages.DISTRICT_UNABLE_RESTOCK_NORMAL  % \
                    {"contact": "sally", "supply_point": "Ntaja", "products": "zi, la"}}


        self.runScript(a)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(req.supply_point, SupplyPoint.objects.get(code="261601"))
            self.assertEqual(StockRequestStatus.STOCKED_OUT, req.status)
            self.assertEqual(StockRequestStatus.STOCKED_OUT, req.response_status)
            self.assertTrue(req.is_pending())
        zi = ProductStock.objects.get(product__sms_code="zi", supply_point=SupplyPoint.objects.get(code="261601"))
        la = ProductStock.objects.get(product__sms_code="la", supply_point=SupplyPoint.objects.get(code="261601"))
        self.assertEqual(zi.quantity, 10)
        self.assertEqual(la.quantity, 15)


    def testEmergencyStockOnHand(self):
        self._setup_users()
        a = """
           16175551000 > eo zi 10 la 300
           16175551000 < %(confirm)s
           16175551004 <  wendy needs emergency products zi 190, also la 60. Respond 'ready 261601' or 'os 261601'
        """ % {"confirm": config.Messages.EMERGENCY_SOH % {"products": "zi la"}}

        self.runScript(a)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(req.supply_point, SupplyPoint.objects.get(code="261601"))
            self.assertEqual(StockRequestStatus.REQUESTED, req.status)
            self.assertEqual("", req.response_status)
            self.assertTrue(req.is_pending())
            if req.product.sms_code == "zi":
                self.assertTrue(req.is_emergency)
            else:
                self.assertEqual("la", req.product.sms_code)
                self.assertFalse(req.is_emergency)
        zi = ProductStock.objects.get(product__sms_code="zi", supply_point=SupplyPoint.objects.get(code="261601"))
        la = ProductStock.objects.get(product__sms_code="la", supply_point=SupplyPoint.objects.get(code="261601"))
        self.assertEqual(zi.quantity, 10)
        self.assertEqual(la.quantity, 300)

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
        """ % {"confirm": config.Messages.HF_UNABLE_RESTOCK_EO %\
                    {"reporter": "sally", "products": "zi"},
               "district": config.Messages.DISTRICT_UNABLE_RESTOCK_EO  % \
                    {"contact": "sally", "supply_point": "Ntaja", "products": "zi"},
               "hsa_notice": config.Messages.HSA_UNABLE_RESTOCK_EO % {"hsa": "wendy", "products": "zi"}}
        self.runScript(a)

    def testEmergencyOrderNoProductsInEmergency(self):
        self._setup_users()
        a = """
           16175551000 > eo zi 400 la 200
           16175551000 < %(confirm)s
           16175551004 < wendy needs emergency products none, also la 160. Respond 'ready 261601' or 'os 261601'
        """ % {"confirm": config.Messages.EMERGENCY_SOH % {"products": "zi la"}}

        self.runScript(a)

    def testEmergencyOrderNoProductsNotInEmergency(self):
        self._setup_users()
        a = """
           16175551000 > eo zi 0 la 0
           16175551000 < %(confirm)s
           16175551001 < wendy is stocked out of and needs: zi 200, la 360. Respond 'ready 261601' or 'os 261601'
        """ % {"confirm": config.Messages.EMERGENCY_SOH % {"products": "zi la"}}

        self.runScript(a)

    def testEmergencyHFStockOut(self):
        self.testEmergencyOrderNoProductsNotInEmergency()
        # the difference here is that only emergency products are
        # reported/escalated
        a = """
           16175551001 > os 261601
           16175551001 < %(confirm)s
           16175551002 < %(district)s
           16175551003 < %(district)s
           16175551000 < %(hsa_notice)s
        """ % {"confirm": config.Messages.HF_UNABLE_RESTOCK_EO %\
                    {"reporter": "sally", "products": "zi, la"},
               "district": config.Messages.DISTRICT_UNABLE_RESTOCK_STOCKOUT  % \
                    {"contact": "sally", "supply_point": "Ntaja", "products": "zi, la"},
               "hsa_notice": config.Messages.HSA_UNABLE_RESTOCK_EO % {"hsa": "wendy", "products": "zi, la"}}
        self.runScript(a)

    def testEmergencyOrderNoProductsNotInEmergencyWithAdditional(self):
        self._setup_users()
        a = """
           16175551000 > eo zi 0 la 0 co 10
           16175551000 < %(confirm)s
           16175551001 < wendy is stocked out of and needs: zi 200, la 360, and additionally: co 430. Respond 'ready 261601' or 'os 261601'
        """ % {"confirm": config.Messages.EMERGENCY_SOH % {"products": "co zi la"}}

        self.runScript(a)

    def testSOHStockout(self):
        self._setup_users()
        a = """
           16175551000 > soh zi 0 co 10 la 0
           16175551000 < %(confirm)s
           16175551001 < %(supervisor)s
           16175551004 < %(supervisor)s
        """ % {"confirm": config.Messages.SOH_ORDER_STOCKOUT_CONFIRM % \
                    {"contact": "wendy", "products": "zi la"},
               "supervisor": config.Messages.SUPERVISOR_SOH_NOTIFICATION_WITH_STOCKOUTS % \
                    {"hsa": "wendy", "products": "co 430, zi 200, la 360",
                     "stockedout_products": "zi la",
                     "hsa_id": "261601"}}
        self.runScript(a)

    def _setup_users(self):
        hsa = create_hsa(self, "16175551000", "wendy", products="co la lb zi")
        ic = create_manager(self, "16175551001", "sally")
        sh = create_manager(self, "16175551004", "robert", config.Roles.HSA_SUPERVISOR)
        im = create_manager(self, "16175551002", "peter", config.Roles.IMCI_COORDINATOR, "26")
        dp = create_manager(self, "16175551003", "ruth", config.Roles.DISTRICT_PHARMACIST, "26")
        return (hsa, ic, sh, im, dp)
