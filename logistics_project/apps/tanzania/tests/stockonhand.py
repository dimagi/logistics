from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user, add_products
from logistics.models import Product, ProductStock, ProductReport
from logistics.util import config
from django.utils import translation
from django.utils.translation import ugettext as _

class TestStockOnHand(TanzaniaTestScriptBase):
        
    def setUp(self):
        super(TestStockOnHand, self).setUp()
        ProductStock.objects.all().delete()
        ProductReport.objects.all().delete()
        
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
        for ps in ProductStock.objects.all():
            self.assertEqual(contact.supply_point, ps.supply_point)
            self.assertTrue(0 != ps.quantity)
        
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
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
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
            +255714774042 > soh fs100md100
            +255714774042 > language en
            +255714774042 < %(language_confirm)s
            +255714774042 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM),
               'language_confirm': _(config.Messages.LANGUAGE_CONFIRM) % {"language": "English"}}
        self.runScript(script)