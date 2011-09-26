from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user, add_products
from logistics.models import Product, ProductStock, ProductReportsHelper
from django.utils.translation import ugettext as _
from django.utils import translation
from logistics.util import config

class TestStockInquiry(TanzaniaTestScriptBase):

    def setUp(self):
        super(TestStockInquiry, self).setUp()
        ProductStock.objects.all().delete()

    def testStockInquiry(self):

        contact = register_user(self, "778", "someone")
        add_products(contact, ["id"])
        p = Product.objects.get(sms_code__iexact="id")
        p.product_code = 'm11111'
        p.save()

        translation.activate("sw")

        script = """
            778 > si m11111 100
            778 < %(stock_inquiry_confirm)s
        """ % {"stock_inquiry_confirm": _(config.Messages.STOCK_INQUIRY_CONFIRM) % {"quantity": "100", "product_name": p.name}}
        self.runScript(script)

        self.assertEqual(1, ProductStock.objects.count())
        for ps in ProductStock.objects.all():
            self.assertEqual(contact.supply_point, ps.supply_point)
            self.assertEqual(100, ps.quantity)