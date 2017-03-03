from __future__ import absolute_import
from logistics.models import StockRequest, SupplyPoint, StockRequestStatus, ProductStock, ProductReport, Product
from rapidsms.models import Contact
from logistics_project.apps.malawi.tests.util import create_manager, report_facility_level_stock
from logistics.util import config
from logistics_project.apps.malawi.tests.facility.base import MalawiFacilityLevelTestBase


class TestFacilityLevelStockOnHandMalawi(MalawiFacilityLevelTestBase):

    def _expected_resupply_level(self, product_code):
        return Product.objects.get(sms_code=product_code).average_monthly_consumption * 2

    def testNoInCharge(self):
        create_manager(self, "+16175551234", "stella", role=config.Roles.IN_CHARGE, supply_point_code="2616")
        a = """
           +16175551234 > soh bc 10
           +16175551234 < %(no_super)s
           """ % {"no_super": config.Messages.NO_IN_CHARGE % {"supply_point": "Machinga"}}
        self.runScript(a)

    def testNoProductsAdded(self):
        Product.objects.filter(type__base_level=config.BaseLevel.FACILITY).delete()
        create_manager(self, "+16175551000", "wendy", role=config.Roles.IN_CHARGE, supply_point_code="2616")
        a = """
           +16175551000 > soh bc 10
           +16175551000 < %(no_products)s
           """ % {"no_products": config.Messages.NO_PRODUCTS_MANAGED}
        self.runScript(a)

    def testReportingHSALevelProduct(self):
        create_manager(self, "+16175551000", "wendy", role=config.Roles.IN_CHARGE, supply_point_code="2616")
        product_code = Product.objects.filter(type__base_level=config.BaseLevel.HSA)[0].sms_code
        for keyword in ("soh", "eo"):
            a = """
                +16175551000 > %(keyword)s %(product_code)s 20
                +16175551000 < %(error)s
            """ % {
                "keyword": keyword,
                "product_code": product_code,
                "error": config.Messages.INVALID_PRODUCTS % {"product_codes": product_code},
            }
            self.runScript(a)

    def testReportingNonExistentProduct(self):
        create_manager(self, "+16175551000", "wendy", role=config.Roles.IN_CHARGE, supply_point_code="2616")
        for keyword in ("soh", "eo"):
            a = """
                +16175551000 > %(keyword)s uvw 10 xyz 20
                +16175551000 < %(error)s
            """ % {
                "keyword": keyword,
                "error": config.Messages.INVALID_PRODUCTS % {"product_codes": "uvw,xyz"},
            }
            self.runScript(a)

    def testBasicSupplyFlow(self):
        ic, sh, he, dp, de, re = self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")
        bc_resupply_amount = bc_resupply_level - 100
        sa_resupply_amount = sa_resupply_level - 500
        report_facility_level_stock(self, ic, "bc 100 sa 500", [de], {"bc": bc_resupply_amount, "sa": sa_resupply_amount})

        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(req.supply_point, ic.supply_point)
            self.assertEqual(req.status, StockRequestStatus.REQUESTED)
            self.assertEqual(req.response_status, "")
            self.assertTrue(req.is_pending())
            self.assertFalse(req.is_emergency)

        bc = ProductStock.objects.get(product__sms_code="bc", supply_point=ic.supply_point)
        sa = ProductStock.objects.get(product__sms_code="sa", supply_point=ic.supply_point)
        self.assertEqual(bc.quantity, 100)
        self.assertEqual(sa.quantity, 500)

        b = """
           +16175551004 > ready 2616
           +16175551004 < %(confirm)s
           +16175551000 < %(facility_notice)s
           +16175551001 < %(facility_notice)s
           +16175551002 < %(facility_notice)s
        """ % {"confirm": config.Messages.APPROVAL_RESPONSE % {"supply_point": "Ntaja"},
               "facility_notice": config.Messages.FACILITY_LEVEL_APPROVAL_NOTICE % {"supply_point": "Ntaja"}}

        self.runScript(b)

        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(req.status, StockRequestStatus.APPROVED)
            self.assertEqual(req.response_status, StockRequestStatus.APPROVED)
            self.assertTrue(req.is_pending())
            self.assertEqual(req.responded_by, de)
            self.assertEqual(req.amount_requested, req.amount_approved)
            self.assertTrue(req.responded_on >= req.requested_on)

        # stocks shouldn't get updated
        self.assertEqual(ProductStock.objects.get(pk=bc.pk).quantity, 100)
        self.assertEqual(ProductStock.objects.get(pk=sa.pk).quantity, 500)

        c = """
           +16175551000 > rec bc %(bc_resupply_amount)s sa %(sa_resupply_amount)s
           +16175551000 < %(confirm)s
        """ % {
            "bc_resupply_amount": bc_resupply_amount,
            "sa_resupply_amount": sa_resupply_amount,
            "confirm": config.Messages.RECEIPT_CONFIRM % {"products": "sa bc"}
        }
        self.runScript(c)

        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(req.status, StockRequestStatus.RECEIVED)
            self.assertEqual(req.response_status, StockRequestStatus.APPROVED)
            self.assertFalse(req.is_pending())
            self.assertEqual(req.received_by, ic)
            self.assertEqual(req.amount_received, req.amount_requested)
            self.assertTrue(req.received_on >= req.responded_on >= req.requested_on)

        # stocks should now be updated
        self.assertEqual(ProductStock.objects.get(pk=bc.pk).quantity, bc_resupply_level)
        self.assertEqual(ProductStock.objects.get(pk=sa.pk).quantity, sa_resupply_level)

        # Second receipt should increase normally

        c = """
           +16175551000 > rec bc 200 sa 400
           +16175551000 < %(confirm)s
        """ % {
            "confirm": config.Messages.RECEIPT_CONFIRM % {"products": "sa bc"}
        }
        self.runScript(c)

        self.assertEqual(ProductStock.objects.get(pk=bc.pk).quantity, bc_resupply_level + 200)
        self.assertEqual(ProductStock.objects.get(pk=sa.pk).quantity, sa_resupply_level + 400)

    def testBackOrdersCanceledByReceipt(self):
        ic, sh, he, dp, de, re = self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")
        bc_resupply_amount = bc_resupply_level - 100
        sa_resupply_amount = sa_resupply_level - 500
        report_facility_level_stock(self, ic, "bc 100 sa 500", [de], {"bc": bc_resupply_amount, "sa": sa_resupply_amount})

        self.assertEqual(2, StockRequest.objects.count())
        c = """
           +16175551000 > rec sa %(sa_resupply_amount)s
           +16175551000 < %(confirm)s
        """ % {
            "sa_resupply_amount": sa_resupply_amount,
            "confirm": config.Messages.RECEIPT_CONFIRM % {"products": "sa"}
        }
        self.runScript(c)
        self.assertEqual(2, StockRequest.objects.count())

        filled = StockRequest.objects.get(product__sms_code='sa')
        canceled = StockRequest.objects.get(product__sms_code='bc')

        # filled order should be marked as such
        self.assertEqual(filled.status, StockRequestStatus.RECEIVED)
        self.assertFalse(filled.is_pending())

        # canceled order should also be marked as such
        self.assertEqual(canceled.status, StockRequestStatus.CANCELED)
        self.assertFalse(canceled.is_pending())

    def testBackOrdersCanceledBySoH(self):
        ic, sh, he, dp, de, re = self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")
        bc_resupply_amount = bc_resupply_level - 100
        sa_resupply_amount = sa_resupply_level - 500
        report_facility_level_stock(self, ic, "bc 100 sa 500", [de], {"bc": bc_resupply_amount, "sa": sa_resupply_amount})

        self.assertEqual(2, StockRequest.objects.count())

        new_sa_resupply_amount = sa_resupply_level - 600
        report_facility_level_stock(self, ic, "sa 600", [de], {"sa": new_sa_resupply_amount})
        self.assertEqual(3, StockRequest.objects.count())

        pending_sa = StockRequest.objects.get(product__sms_code='sa', status=StockRequestStatus.REQUESTED)
        canceled_sa = StockRequest.objects.get(product__sms_code='sa', status=StockRequestStatus.CANCELED)
        canceled_bc = StockRequest.objects.get(product__sms_code='bc')

        self.assertEqual(pending_sa.amount_requested, new_sa_resupply_amount)
        self.assertEqual(canceled_sa.canceled_for, pending_sa)
        self.assertEqual(canceled_bc.canceled_for, None)

    def testAppendStockOnHand(self):
        # with the removal of back orders this test is sort of redundant with testBackOrdersCanceledBySoH
        # though is a bit more expansive
        ic, sh, he, dp, de, re = self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")
        sb_resupply_level = self._expected_resupply_level("sb")

        bc_resupply_amount = bc_resupply_level - 100
        sa_resupply_amount = sa_resupply_level - 500
        report_facility_level_stock(self, ic, "bc 100 sa 500", [de], {"bc": bc_resupply_amount, "sa": sa_resupply_amount})
        self.assertEqual(2, StockRequest.objects.count())

        bc_resupply_amount = bc_resupply_level - 90
        sb_resupply_amount = sb_resupply_level - 600
        report_facility_level_stock(self, ic, "bc 90 sb 600", [de], {"bc": bc_resupply_amount, "sb": sb_resupply_amount})
        self.assertEqual(4, StockRequest.objects.count())
        self.assertEqual(2, StockRequest.objects.filter(status=StockRequestStatus.REQUESTED).count())
        self.assertEqual(2, StockRequest.objects.filter(status=StockRequestStatus.CANCELED).count())

        b = """
           +16175551004 > ready 2616
           +16175551004 < %(confirm)s
           +16175551000 < %(facility_notice)s
           +16175551001 < %(facility_notice)s
           +16175551002 < %(facility_notice)s
        """ % {"confirm": config.Messages.APPROVAL_RESPONSE % {"supply_point": "Ntaja"},
               "facility_notice": config.Messages.FACILITY_LEVEL_APPROVAL_NOTICE % {"supply_point": "Ntaja"}}

        self.runScript(b)
        self.assertEqual(2, StockRequest.objects.filter(status=StockRequestStatus.APPROVED).count())
        self.assertEqual(2, StockRequest.objects.filter(status=StockRequestStatus.CANCELED).count())

    def testSOHBeforeReceipt(self):
        ic, sh, he, dp, de, re = self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")
        bc_resupply_amount = bc_resupply_level - 100
        sa_resupply_amount = sa_resupply_level - 500
        report_facility_level_stock(self, ic, "bc 100 sa 500", [de], {"bc": bc_resupply_amount, "sa": sa_resupply_amount})

        bc = ProductStock.objects.get(product__sms_code="bc", supply_point=ic.supply_point)
        sa = ProductStock.objects.get(product__sms_code="sa", supply_point=ic.supply_point)
        self.assertEqual(2, StockRequest.objects.filter(status=StockRequestStatus.REQUESTED).count())

        b = """
           +16175551004 > ready 2616
           +16175551004 < %(confirm)s
           +16175551000 < %(facility_notice)s
           +16175551001 < %(facility_notice)s
           +16175551002 < %(facility_notice)s
        """ % {"confirm": config.Messages.APPROVAL_RESPONSE % {"supply_point": "Ntaja"},
               "facility_notice": config.Messages.FACILITY_LEVEL_APPROVAL_NOTICE % {"supply_point": "Ntaja"}}

        self.runScript(b)
        self.assertEqual(2, StockRequest.objects.filter(status=StockRequestStatus.APPROVED).count())

        report_facility_level_stock(self, ic, "bc 100 sa 500", [de], {"bc": bc_resupply_amount, "sa": sa_resupply_amount})
        self.assertEqual(2, StockRequest.objects.filter(status=StockRequestStatus.REQUESTED).count())

        c = """
           +16175551000 > rec bc %(bc_resupply_amount)s sa %(sa_resupply_amount)s
           +16175551000 < %(confirm)s
        """ % {
            "bc_resupply_amount": bc_resupply_amount,
            "sa_resupply_amount": sa_resupply_amount,
            "confirm": config.Messages.RECEIPT_CONFIRM % {"products": "sa bc"}
        }
        self.runScript(c)

        self.assertEqual(bc_resupply_level, ProductStock.objects.get(pk=bc.pk).quantity)
        self.assertEqual(sa_resupply_level, ProductStock.objects.get(pk=sa.pk).quantity)
        self.assertEqual(2, StockRequest.objects.filter(status=StockRequestStatus.RECEIVED).count())

    def testNothingToFill(self):
        self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")

        a = """
            +16175551000 > soh bc %(bc_resupply_level)s sa %(sa_resupply_level)s
            +16175551000 < %(response)s
            +16175551004 < %(super)s
        """ % {
            "bc_resupply_level": bc_resupply_level,
            "sa_resupply_level": sa_resupply_level,
            "response": config.Messages.SOH_ORDER_CONFIRM_NOTHING_TO_DO % {"contact": "Ntaja", "products": "sa bc"},
            "super": config.Messages.SUPERVISOR_SOH_NOTIFICATION_NOTHING_TO_DO % {"supply_point": "Ntaja"}
        }
        self.runScript(a)
        self.assertEqual(0, StockRequest.objects.count())

    def testStockoutSupplyFlow(self):
        ic, sh, he, dp, de, re = self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")
        bc_resupply_amount = bc_resupply_level - 100
        sa_resupply_amount = sa_resupply_level - 500
        report_facility_level_stock(self, ic, "bc 100 sa 500", [de], {"bc": bc_resupply_amount, "sa": sa_resupply_amount})

        a = """
           +16175551004 > os 2616
           +16175551004 < %(confirm)s
           +16175551000 < %(facility_notice)s
           +16175551001 < %(facility_notice)s
           +16175551002 < %(facility_notice)s
           +16175551005 < %(regional_notice)s
        """ % {"confirm": config.Messages.FACILITY_LEVEL_OS_EO_RESPONSE % {"products": "sa, bc"},
               "facility_notice": config.Messages.UNABLE_RESTOCK_FACILITY_NOTIFICATION % {"supply_point": "Ntaja"},
               "regional_notice": config.Messages.UNABLE_RESTOCK_NORMAL_ZONE_ESCALATION %
                    {"contact": de.name, "supply_point": "Machinga", "products": "sa, bc"}}

        self.runScript(a)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(req.supply_point, ic.supply_point)
            self.assertEqual(req.status, StockRequestStatus.STOCKED_OUT)
            self.assertEqual(req.response_status, StockRequestStatus.STOCKED_OUT)
            self.assertTrue(req.is_pending())
        bc = ProductStock.objects.get(product__sms_code="bc", supply_point=ic.supply_point)
        sa = ProductStock.objects.get(product__sms_code="sa", supply_point=ic.supply_point)
        self.assertEqual(bc.quantity, 100)
        self.assertEqual(sa.quantity, 500)

    def testEmergencyStockOnHand(self):
        ic, sh, he, dp, de, re = self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")
        bc_resupply_amount = bc_resupply_level - 5
        sa_resupply_amount = sa_resupply_level - 500
        a = """
           +16175551000 > eo bc 5 sa 500
           +16175551000 < %(confirm)s
           +16175551004 < %(district_notice)s
        """ % {
            "confirm": config.Messages.FACILITY_LEVEL_EMERGENCY_SOH % {"products": "sa bc"},
            "district_notice": config.Messages.SUPERVISOR_EMERGENCY_SOH_NOTIFICATION % {
                    "supply_point": "Ntaja",
                    "emergency_products": "bc %s" % bc_resupply_amount,
                    "normal_products": "sa %s" % sa_resupply_amount,
                    "supply_point_code": "2616",
                }
        }

        self.runScript(a)
        self.assertEqual(2, StockRequest.objects.count())
        for req in StockRequest.objects.all():
            self.assertEqual(req.supply_point, ic.supply_point)
            self.assertEqual(req.status, StockRequestStatus.REQUESTED)
            self.assertEqual(req.response_status, "")
            self.assertTrue(req.is_pending())
            if req.product.sms_code == "bc":
                self.assertTrue(req.is_emergency)
            else:
                self.assertEqual(req.product.sms_code, "sa")
                self.assertFalse(req.is_emergency)
        bc = ProductStock.objects.get(product__sms_code="bc", supply_point=ic.supply_point)
        sa = ProductStock.objects.get(product__sms_code="sa", supply_point=ic.supply_point)
        self.assertEqual(bc.quantity, 5)
        self.assertEqual(sa.quantity, 500)

    def testEmergencyStockOut(self):
        self.testEmergencyStockOnHand()
        # the difference here is that only emergency products are
        # reported/escalated
        a = """
           +16175551004 > os 2616
           +16175551004 < %(confirm)s
           +16175551000 < %(facility_notice)s
           +16175551001 < %(facility_notice)s
           +16175551002 < %(facility_notice)s
           +16175551005 < %(regional_notice)s
        """ % {"confirm": config.Messages.FACILITY_LEVEL_OS_EO_RESPONSE % {"products": "bc"},
               "regional_notice": config.Messages.UNABLE_RESTOCK_EO_ZONE_ESCALATION  %
                    {"contact": "peter", "supply_point": "Machinga", "products": "bc"},
               "facility_notice": config.Messages.UNABLE_RESTOCK_EO_FACILITY_NOTIFICATION % {"supply_point": "Ntaja", "products": "bc"}}
        self.runScript(a)

    def testEmergencyOrderNoProductsInEmergency(self):
        ic, sh, he, dp, de, re = self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")
        sa_resupply_amount = sa_resupply_level - 500
        a = """
           +16175551000 > eo bc %(bc_resupply_level)s sa 500
           +16175551000 < %(confirm)s
           +16175551004 < %(district_notice)s
        """ % {
            "bc_resupply_level": bc_resupply_level,
            "confirm": config.Messages.FACILITY_LEVEL_EMERGENCY_SOH % {"products": "sa bc"},
            "district_notice": config.Messages.SUPERVISOR_EMERGENCY_SOH_NOTIFICATION % {
                    "supply_point": "Ntaja",
                    "emergency_products": "none",
                    "normal_products": "sa %s" % sa_resupply_amount,
                    "supply_point_code": "2616",
                }
        }
        self.runScript(a)

    def testEmergencyOrderStockout(self):
        ic, sh, he, dp, de, re = self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")
        a = """
           +16175551000 > eo bc 0 sa 0
           +16175551000 < %(confirm)s
           +16175551004 < %(district_notice)s
        """ % {
            "confirm": config.Messages.FACILITY_LEVEL_EMERGENCY_SOH % {"products": "sa bc"},
            "district_notice": config.Messages.EMERGENCY_STOCKOUT_NO_ADDITIONAL % {
                    "supply_point": "Ntaja",
                    "stockouts": "sa %s, bc %s" % (sa_resupply_level, bc_resupply_level),
                    "supply_point_code": "2616",
                }
        }
        self.runScript(a)

    def testEmergencyOrderStockOutAndDistrictStockout(self):
        self.testEmergencyOrderStockout()
        # the difference here is that only emergency products are
        # reported/escalated
        a = """
           +16175551004 > os 2616
           +16175551004 < %(confirm)s
           +16175551000 < %(facility_notice)s
           +16175551001 < %(facility_notice)s
           +16175551002 < %(facility_notice)s
           +16175551005 < %(regional_notice)s
        """ % {"confirm": config.Messages.FACILITY_LEVEL_OS_EO_RESPONSE % {"products": "sa, bc"},
               "regional_notice": config.Messages.UNABLE_RESTOCK_STOCKOUT_ZONE_ESCALATION  %
                    {"contact": "peter", "supply_point": "Machinga", "products": "sa, bc"},
               "facility_notice": config.Messages.UNABLE_RESTOCK_EO_FACILITY_NOTIFICATION % {"supply_point": "Ntaja", "products": "sa, bc"}}
        self.runScript(a)

    def testEmergencyOrderStockoutWithAdditional(self):
        ic, sh, he, dp, de, re = self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")
        sb_resupply_level = self._expected_resupply_level("sb")
        a = """
           +16175551000 > eo bc 0 sa 0 sb 500
           +16175551000 < %(confirm)s
           +16175551004 < %(district_notice)s
        """ % {
            "confirm": config.Messages.FACILITY_LEVEL_EMERGENCY_SOH % {"products": "sb sa bc"},
            "district_notice": config.Messages.EMERGENCY_STOCKOUT % {
                    "supply_point": "Ntaja",
                    "stockouts": "sa %s, bc %s" % (sa_resupply_level, bc_resupply_level),
                    "normal_products": "sb %s" % (sb_resupply_level - 500),
                    "supply_point_code": "2616",
                }
        }
        self.runScript(a)

    def testSOHStockout(self):
        ic, sh, he, dp, de, re = self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")
        sb_resupply_level = self._expected_resupply_level("sb")
        a = """
           +16175551000 > soh bc 0 sa 500 sb 0
           +16175551000 < %(confirm)s
           +16175551004 < %(district_notice)s
        """ % {
            "confirm": config.Messages.SOH_FACILITY_LEVEL_ORDER_STOCKOUT_CONFIRM % {"products": "sb bc"},
            "district_notice": config.Messages.SUPERVISOR_FACILITY_LEVEL_SOH_NOTIFICATION_WITH_STOCKOUTS % {
                "supply_point": "Ntaja",
                "products": "sb %s, sa %s, bc %s" % (sb_resupply_level, (sa_resupply_level - 500), bc_resupply_level),
                "stockedout_products": "sb bc",
                "supply_point_code": "2616",
            }
        }
        self.runScript(a)

    def testMaxSupplyLevel(self):
        ic, sh, he, dp, de, re = self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")
        bc_resupply_amount = bc_resupply_level - 100
        sa_resupply_amount = sa_resupply_level - 500
        # The "too much stock" validation step requires ProductStock entries to exist
        report_facility_level_stock(self, ic, "bc 100 sa 500", [de], {"bc": bc_resupply_amount, "sa": sa_resupply_amount})

        keyword_response_pairs = (
            ('soh', config.Messages.SOH_FACILITY_LEVEL_ORDER_CONFIRM % {"products": "sa bc"}),
            ('eo', config.Messages.FACILITY_LEVEL_EMERGENCY_SOH % {"products": "sa bc"}),
            ('rec', config.Messages.RECEIPT_CONFIRM % {"products": "sa bc"}),
        )

        for keyword, response in keyword_response_pairs:
            report_count = ProductReport.objects.count()
            a = """
               +16175551000 > %(keyword)s bc 100000000 sa 15
               +16175551000 < %(too_much)s
            """ % {
                'keyword': keyword,
                "too_much": config.Messages.TOO_MUCH_STOCK % {'keyword': keyword},
            }
            self.runScript(a)
            self.assertEqual(report_count, ProductReport.objects.count())

            # the second time it should go through
            a = """
               +16175551000 > %(keyword)s bc 100000000 sa 15
               +16175551000 < %(response)s
            """ % {
                'keyword': keyword,
                'response': response,
            }
            self.runScript(a)
            # one new report for each product
            self.assertEqual(report_count + 2, ProductReport.objects.count())

    def testSoHKeepDupes(self):
        ProductReport.objects.all().delete()

        ic, sh, he, dp, de, re = self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")
        bc_resupply_amount = bc_resupply_level - 100
        sa_resupply_amount = sa_resupply_level - 500

        report_facility_level_stock(self, ic, "bc 100 sa 500", [de], {"bc": bc_resupply_amount, "sa": sa_resupply_amount})
        self.assertEqual(2, ProductReport.objects.count())

        report_facility_level_stock(self, ic, "bc 100 sa 500", [de], {"bc": bc_resupply_amount, "sa": sa_resupply_amount})
        self.assertEqual(4, ProductReport.objects.count())

        report_facility_level_stock(self, ic, "bc 100 sa 500", [de], {"bc": bc_resupply_amount, "sa": sa_resupply_amount})
        self.assertEqual(6, ProductReport.objects.count())

    def assertProductStock(self, product_code, supply_point_code, quantity):
        ps = ProductStock.objects.get(product__sms_code=product_code, supply_point__code=supply_point_code)
        self.assertEqual(ps.quantity, quantity)

    def testReportingDuringFridgeMalfunction(self):
        ic, sh, he, dp, de, re = self._setup_users()
        bc_resupply_level = self._expected_resupply_level("bc")
        sa_resupply_level = self._expected_resupply_level("sa")

        report_facility_level_stock(self, ic, "bc 50 sa 500", [de], {"bc": bc_resupply_level - 50, "sa": sa_resupply_level - 500})
        self.assertProductStock("bc", "2616", 50)
        self.assertProductStock("sa", "2616", 500)
        self.assertEqual(2, ProductReport.objects.count())

        self.runScript("""
                +16175551000 > rm 1
                +16175551000 < %(facility_response)s
                +16175551004 < %(district_response)s
                +16175551000 > soh bc 100 sa 400
                +16175551000 < %(error_response)s
                +16175551000 > eo bc 100 sa 400
                +16175551000 < %(error_response)s
            """ % {
                "facility_response": config.Messages.FRIDGE_BROKEN_RESPONSE % {'reason': config.Messages.FRIDGE_BROKEN_NO_GAS},
                "district_response": config.Messages.FRIDGE_BROKEN_NOTIFICATION % {'reason': config.Messages.FRIDGE_BROKEN_NO_GAS, 'facility': '2616'},
                "error_response": config.Messages.FRIDGE_BROKEN,
            }
        )

        self.assertProductStock("bc", "2616", 50)
        self.assertProductStock("sa", "2616", 500)
        self.assertEqual(2, ProductReport.objects.count())

        self.runScript("""
                +16175551000 > rf
                +16175551000 < %(facility_response)s
            """ % {
                "facility_response": config.Messages.FRIDGE_FIXED_RESPONSE,
            }
        )

        report_facility_level_stock(self, ic, "bc 100 sa 400", [de], {"bc": bc_resupply_level - 100, "sa": sa_resupply_level - 400})
        self.assertProductStock("bc", "2616", 100)
        self.assertProductStock("sa", "2616", 400)
        self.assertEqual(4, ProductReport.objects.count())
