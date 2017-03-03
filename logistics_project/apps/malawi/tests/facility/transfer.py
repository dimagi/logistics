from __future__ import absolute_import
from logistics.models import Product, ProductStock, SupplyPoint, StockTransfer, StockTransferStatus
from logistics.util import config
from logistics_project.apps.malawi.tests.util import create_manager
from logistics_project.apps.malawi.tests.facility.base import MalawiFacilityLevelTestBase


class TestFacilityLevelTransfer(MalawiFacilityLevelTestBase):
    
    def testValidation(self):
        self._setup_users()
        a = """
           +16175551004 > give 2616 bc 20
           +16175551004 < %(bad_role)s
           +16175551001 > give 26 bc 20
           +16175551001 < %(not_found)s
        """ % {
            "bad_role": config.Messages.UNSUPPORTED_OPERATION,
            "not_found": config.Messages.UNKNOWN_FACILITY % {"supply_point_code": "26"},
        }
        self.runScript(a)

    def testBasicTransfer(self):
        ic1 = self._setup_users()[0]
        ic2a = create_manager(self, "+16175552000", "alex", config.Roles.IN_CHARGE, "2601")
        ic2b = create_manager(self, "+16175552001", "bob", config.Roles.HSA_SUPERVISOR, "2601")
        ic2c = create_manager(self, "+16175552002", "charles", config.Roles.EPI_FOCAL, "2601")

        a = """
           +16175551000 > soh bc 600
           +16175551000 < %(response)s
        """ % {
            "response": config.Messages.SOH_ORDER_CONFIRM_NOTHING_TO_DO % {"contact": "Ntaja", "products": "bc"},
        }
        self.runScript(a)

        a = """
           +16175552000 > soh bc 500
           +16175552000 < %(response)s
        """ % {
            "response": config.Messages.SOH_ORDER_CONFIRM_NOTHING_TO_DO % {"contact": "Chamba", "products": "bc"},
        }
        self.runScript(a)

        stock_from = ProductStock.objects.get(supply_point=ic1.supply_point, product__sms_code="bc")
        stock_to = ProductStock.objects.get(supply_point=ic2a.supply_point, product__sms_code="bc")
        self.assertEqual(stock_from.quantity, 600)
        self.assertEqual(stock_to.quantity, 500)

        b = """
           +16175551000 > give 2601 bc 60
           +16175551000 < %(response)s
           +16175552000 < %(confirm)s
           +16175552001 < %(confirm)s
           +16175552002 < %(confirm)s
        """ % {
            "response": config.Messages.TRANSFER_RESPONSE % {
                "giver": "Ntaja",
                "receiver": "Chamba", 
                "reporter": ic1.name,
                "products": "bc 60",
            },
            "confirm": config.Messages.TRANSFER_CONFIRM % {
                "giver": "Ntaja",
                "products": "bc 60",
            }
        }
        self.runScript(b)

        self.assertEqual(540, ProductStock.objects.get(pk=stock_from.pk).quantity)
        self.assertEqual(500, ProductStock.objects.get(pk=stock_to.pk).quantity)
        [st] = StockTransfer.objects.all()
        self.assertTrue(st.is_pending())
        self.assertEqual(st.product.sms_code, "bc")
        self.assertEqual(st.amount, 60)
        self.assertEqual(st.giver, ic1.supply_point)
        self.assertEqual(st.receiver, ic2a.supply_point)

        c = """
           +16175552000 > confirm
           +16175552000 < %(response)s
        """ % {
            "response": config.Messages.CONFIRM_RESPONSE % {
                "receiver": "Chamba",
                "products": "bc 60",
            }
        }
        self.runScript(c)

        self.assertEqual(540, ProductStock.objects.get(pk=stock_from.pk).quantity)
        self.assertEqual(560, ProductStock.objects.get(pk=stock_to.pk).quantity)
        [st] = StockTransfer.objects.all()
        self.assertTrue(st.is_closed())

    def testTransferFromReceipt(self):
        ic1 = self._setup_users()[0]
        ic2 = create_manager(self, "+16175552000", "alex", config.Roles.IN_CHARGE, "2601")

        a = """
           +16175552000 > rec bc 100 sa 250 from 2616
           +16175552000 < %(response)s
        """ % {
            "response": config.Messages.RECEIPT_FROM_CONFIRM % {"supplier": "2616", "products": "sa bc"},
        }
        self.runScript(a)
        self.assertEqual(2, StockTransfer.objects.count())
        self.assertEqual(100, StockTransfer.objects.get(product__sms_code="bc").amount)
        self.assertEqual(250, StockTransfer.objects.get(product__sms_code="sa").amount)
        for transfer in StockTransfer.objects.all():
            self.assertEqual(transfer.giver, ic1.supply_point)
            self.assertEqual(transfer.giver_unknown, "")
            self.assertEqual(transfer.receiver, ic2.supply_point)
            self.assertEqual(transfer.status, StockTransferStatus.CONFIRMED)
            self.assertEqual(transfer.initiated_on, None)

    def testTransferFromReceiptNoSupplyPoint(self):
        ic = self._setup_users()[0]
        a = """
           +16175551000 > rec bc 100 sa 250 from unknown
           +16175551000 < %(response)s
        """ % {
            "response": config.Messages.RECEIPT_FROM_CONFIRM % {"supplier": "unknown", "products": "sa bc"},
        }
        self.runScript(a)
        self.assertEqual(2, StockTransfer.objects.count())
        self.assertEqual(100, StockTransfer.objects.get(product__sms_code="bc").amount)
        self.assertEqual(250, StockTransfer.objects.get(product__sms_code="sa").amount)
        for transfer in StockTransfer.objects.all():
            self.assertEqual(transfer.giver, None)
            self.assertEqual(transfer.giver_unknown, "unknown")
            self.assertEqual(transfer.receiver, ic.supply_point)
            self.assertEqual(transfer.status, StockTransferStatus.CONFIRMED)
            self.assertEqual(transfer.initiated_on, None)

    def testHSALevelProduct(self):
        ic1 = self._setup_users()[0]
        product_code = Product.objects.filter(type__base_level=config.BaseLevel.HSA)[0].sms_code
        self.runScript("""
            +16175551000 > give 2601 %(product_code)s 20
            +16175551000 < %(error)s
        """ % {
            "product_code": product_code,
            "error": config.Messages.INVALID_PRODUCTS % {"product_codes": product_code},
        })

    def testNonExistentProduct(self):
        ic1 = self._setup_users()[0]
        self.runScript("""
            +16175551000 > give 2601 uvw 10 xyz 20
            +16175551000 < %(error)s
        """ % {
            "error": config.Messages.INVALID_PRODUCTS % {"product_codes": "uvw,xyz"},
        })
