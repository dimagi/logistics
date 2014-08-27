from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user, add_products
from logistics.models import Product, ProductStock, ProductReport, SupplyPoint
from logistics.util import config
from django.utils import translation
from django.utils.translation import ugettext as _
from logistics_project.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusValues, SupplyPointStatusTypes

class TestStockOnHand(TanzaniaTestScriptBase):
        
    def setUp(self):
        super(TestStockOnHand, self).setUp()
        ProductStock.objects.all().delete()
        ProductReport.objects.all().delete()
        SupplyPointStatus.objects.all().delete()
        
    def testStockOnHand(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone")
        add_products(contact, ["id", "dp", "ip"])
        
        script = """
            778 > Hmk Id 400 Dp 569 Ip 678
            778 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
        self.runScript(script)
        self.assertEqual(3, ProductReport.objects.count())
        self.assertEqual(3, ProductStock.objects.count())
        
        # check created statuses
        self.assertEqual(2, SupplyPointStatus.objects.count())
        soh_status = SupplyPointStatus.objects.get(status_type=SupplyPointStatusTypes.SOH_FACILITY)
        self.assertEqual(contact.supply_point, soh_status.supply_point)
        self.assertEqual(SupplyPointStatusValues.SUBMITTED, soh_status.status_value)
        la_status = SupplyPointStatus.objects.get(status_type=SupplyPointStatusTypes.LOSS_ADJUSTMENT_FACILITY)
        self.assertEqual(contact.supply_point, la_status.supply_point)
        self.assertEqual(SupplyPointStatusValues.REMINDER_SENT, la_status.status_value)
        
        for ps in ProductStock.objects.all():
            self.assertEqual(contact.supply_point, ps.supply_point)
            self.assertTrue(0 != ps.quantity)
        
    def testStockOnHandStockouts(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone")
        add_products(contact, ["id", "dp", "ip"])
        script = """
            778 > Hmk Id 0 Dp 0 Ip 0
            778 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
        self.runScript(script)
        self.assertEqual(3, ProductReport.objects.count())
        self.assertEqual(3, ProductStock.objects.count())

        for ps in ProductStock.objects.all():
            self.assertEqual(contact.supply_point, ps.supply_point)
            self.assertEqual(0, ps.quantity)

    def testStockOnHandStockoutsUpdate(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone")
        add_products(contact, ["id", "dp", "ip"])

        prod_amt_configs = [
            (('Id', 100), ('Dp', 200), ('Ip', 300)),
            (('Id', 0), ('Dp', 100), ('Ip', 200)),
            (('Id', 100), ('Dp', 0), ('Ip', 0)),
            (('Id', 50), ('Dp', 150), ('Ip', 250)),
            (('Id', 0), ('Dp', 0), ('Ip', 0)),
        ]
        pkmax = -1
        for prod_amt_config in prod_amt_configs:
            this_pkmax = pkmax
            product_string = ' '.join(['{p} {v}'.format(p=p, v=v) for p, v in prod_amt_config])
            script = """
                778 > Hmk {products}
                778 < {soh_confirm}
            """.format(
                products=product_string,
                soh_confirm= _(config.Messages.SOH_CONFIRM)
            )
            self.runScript(script)
            self.assertEqual(3, ProductReport.objects.filter(pk__gt=pkmax).count())
            self.assertEqual(3, ProductStock.objects.count())
            for code, amt in prod_amt_config:
                ps = ProductStock.objects.get(product__sms_code__iexact=code)
                self.assertEqual(amt, ps.quantity)
                pr = ProductReport.objects.get(pk__gt=pkmax, product__sms_code__iexact=code)
                self.assertEqual(amt, ps.quantity)
                this_pkmax = max(this_pkmax, pr.pk)
            pkmax = max(this_pkmax, pkmax)

    def testStockOnHandPartialReport(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone")
        add_products(contact, ["id", "dp", "fs", "md", "ff", "dx", "bp", "pc", "qi"])
        script = """
            778 > Hmk Id 400
            778 < Asante someone kwa kutuma taarifa za akiba ya vifaa vilivyopo vya VETA 1, bado taarifa za bp dp dx ff fs md pc qi
        """
        self.runScript(script)

        script = """
            778 > Hmk Dp 569 ip 454 ff 5655
            778 < Asante someone kwa kutuma taarifa za akiba ya vifaa vilivyopo vya VETA 1, bado taarifa za bp dx fs md pc qi
        """
        self.runScript(script)

        script = """
            778 > Hmk Bp 343 Dx 565 Fs 2322 Md 100 Pc 8778 Qi 34
            778 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
        self.runScript(script)

    def testProductAliases(self):
        translation.activate("sw")

        contact = register_user(self, "778", "someone")
        add_products(contact, ["id", "dp", "ip"])
        script = """
            778 > Hmk iucd 400
            778 < Asante someone kwa kutuma taarifa za akiba ya vifaa vilivyopo vya VETA 1, bado taarifa za dp ip
        """
        self.runScript(script)
        script = """
            778 > Hmk Depo 569
            778 < Asante someone kwa kutuma taarifa za akiba ya vifaa vilivyopo vya VETA 1, bado taarifa za ip
        """
        self.runScript(script)

        script = """
            778 > Hmk IMPL 678
            778 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
        self.runScript(script)

    def testStockOnHandDelimitersStandard(self):
        translation.activate("sw")
        contact = register_user(self, "+255714774042", "someone")
        product_codes = ["fs", "md", "ff", "dx", "bp", "pc", "qi"]
        add_products(contact, product_codes)

        #standard spacing
        script = """
            +255714774042 > hmk fs100 md100 ff100 dx100 bp100 pc100 qi100
            +255714774042 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
        self.runScript(script)

    def testStockOnHandDelimitersNoSpaces(self):
        translation.activate("sw")
        contact = register_user(self, "+255714774042", "someone")
        product_codes = ["fs", "md", "ff", "dx", "bp", "pc", "qi"]
        add_products(contact, product_codes)

        #no spaces
        script = """
            +255714774042 > hmk fs100md100ff100dx100bp100pc100qi100
            +255714774042 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
        self.runScript(script)

    def testStockOnHandDelimitersMixedSpacing(self):
        translation.activate("sw")
        contact = register_user(self, "+255714774042", "someone")
        product_codes = ["fs", "md", "ff", "dx", "bp", "pc", "qi"]
        add_products(contact, product_codes)

        #no spaces
        script = """
            +255714774042 > hmk fs100 md 100 ff100 dx  100bp   100 pc100 qi100
            +255714774042 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
        self.runScript(script)

    def testStockOnHandDelimitersAllSpacedOut(self):
        translation.activate("sw")
        contact = register_user(self, "+255714774042", "someone")
        product_codes = ["fs", "md", "ff", "dx", "bp", "pc", "qi"]
        add_products(contact, product_codes)

        #all space delimited
        script = """
            +255714774042 > hmk fs 100 md 100 ff 100 dx 100 bp 100 pc 100 qi 100
            +255714774042 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
        self.runScript(script)

    def testStockOnHandDelimitersCommas(self):
        translation.activate("sw")
        contact = register_user(self, "+255714774042", "someone")
        product_codes = ["fs", "md", "ff"]
        add_products(contact, product_codes)

        #commas
        script = """
            +255714774042 > hmk fs100,md100,ff100
            +255714774042 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
        self.runScript(script)

    def testStockOnHandDelimitersCommasAndSpaces(self):
        translation.activate("sw")
        contact = register_user(self, "+255714774042", "someone")
        product_codes = ["fs", "md", "ff"]
        add_products(contact, product_codes)

        #commas
        script = """
            +255714774042 > hmk fs100, md100, ff100
            +255714774042 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
        self.runScript(script)

    def testStockOnHandDelimitersExtraSpaces(self):
        translation.activate("sw")
        contact = register_user(self, "+255714774042", "someone")
        product_codes = ["fs", "md", "ff", "pc"]
        add_products(contact, product_codes)

        #extra spaces
        script = """
            +255714774042 > hmk fs  100   md    100     ff      100       pc        100
            +255714774042 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
        self.runScript(script)

    def testStockOnHandMixedDelimitersAndSpacing(self):
        translation.activate("sw")
        contact = register_user(self, "+255714774042", "someone")
        product_codes = ["fs", "md", "ff", "pc", "qi", "bp", "dx"]
        add_products(contact, product_codes)

        #mixed - commas, spacing
        script = """
            +255714774042 > hmk fs100 , md100,ff 100 pc  100  qi,       1000,bp, 100, dx,100
            +255714774042 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_PARTIAL_CONFIRM) % {"contact_name": "someone", "facility_name": "VETA 1", "product_list": "bp dx qi"}}
        self.runScript(script)

    def testStockOnHandKeywordsandLanguageSwahili(self):
        translation.activate("sw")
        contact = register_user(self, "+255714774042", "someone")
        product_codes = ["fs", "md"]
        add_products(contact, product_codes)

        script = """
            +255714774042 > hmk fs100md100
            +255714774042 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
        self.runScript(script)

    def testStockOnHandKeywordsandLanguageEnglish(self):
        translation.activate("en")
        contact = register_user(self, "+255714774042", "someone")
        product_codes = ["fs", "md"]
        add_products(contact, product_codes)

        script = """
            +255714774042 > language en
            +255714774042 < %(language_confirm)s
        """ % {'language_confirm': _(config.Messages.LANGUAGE_CONFIRM) % {"language": "English"}}
        self.runScript(script)

        """
            +255714774042 > soh fs100md100
            +255714774042 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}

        self.runScript(script)