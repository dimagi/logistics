from logistics.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics.apps.tanzania.tests.util import register_user, add_products
from logistics.apps.logistics.models import Product, ProductStock
from django.utils.translation import ugettext as _
from logistics.apps.logistics.util import config
from django.utils import translation
from logistics.apps.logistics.models import SupplyPoint
from logistics.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues

class TestDelivery(TanzaniaTestScriptBase):
        
    def setUp(self):
        super(TestDelivery, self).setUp()
        ProductStock.objects.all().delete()
        
    def testDeliveryReceivedNoQuantitiesReported(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone", "d10001")

        script = """
            778 > nimepokea
            778 < %(received_message)s
            """ % {'received_message': _(config.Messages.DELIVERY_PARTIAL_CONFIRM)}
        self.runScript(script)

        sp = SupplyPoint.objects.get(code="D10001")
        sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                         status_type="del_fac").order_by("-status_date")[0]

        self.assertEqual(SupplyPointStatusValues.RECEIVED, sps.status_value)
        self.assertEqual(SupplyPointStatusTypes.DELIVERY_FACILITY, sps.status_type)

    def testDeliveryReceivedQuantitiesReported(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone", "d10001")
        add_products(contact, ["id", "dp", "ip"])
        
        script = """
            778 > nimepokea Id 400 Dp 569 Ip 678
            778 < %(received_message)s
            """ % {'received_message': _(config.Messages.DELIVERED_CONFIRM) % {"reply_list":"dp,id,ip"}}
        self.runScript(script)
        self.assertEqual(3, ProductStock.objects.count())
        for ps in ProductStock.objects.all():
            self.assertEqual(contact.supply_point, ps.supply_point)
            self.assertTrue(0 != ps.quantity)

    def testDeliveryNotReceived(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone", "d10001")

        script = """
            778 > sijapokea
            778 < %(not_received_message)s
            """ % {'not_received_message': _(config.Messages.NOT_DELIVERED_CONFIRM)}
        self.runScript(script)

        sp = SupplyPoint.objects.get(code="D10001")
        sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                         status_type="del_fac").order_by("-status_date")[0]

        self.assertEqual(SupplyPointStatusValues.NOT_RECEIVED, sps.status_value)
        self.assertEqual(SupplyPointStatusTypes.DELIVERY_FACILITY, sps.status_type)

    def testDeliveryReportError(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone", "d10001")
        add_products(contact, ["id", "dp", "ip"])

        script = """
            778 > nimepokea Ig 400 Dp 569 Ip 678
            778 < %(error_message)s
            """ % {'error_message': _(config.Messages.INVALID_PRODUCT_CODE) % {"code":"ig"}}
        self.runScript(script)

    #def testDeliveryFacility
    #TODO should record a SupplyPointStatus and send out a notification to all the District's sub-facilities.

