from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user, add_products
from logistics.models import Product, ProductStock
from django.utils.translation import ugettext as _
from logistics.util import config
from django.utils import translation
from logistics.models import SupplyPoint
from logistics_project.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues
from datetime import datetime
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Contact

class TestDelivery(TanzaniaTestScriptBase):
        
    def setUp(self):
        super(TestDelivery, self).setUp()
        ProductStock.objects.all().delete()
        Contact.objects.all().delete()
        Message.objects.all().delete()
        
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

    def testDeliveryDistrictReceived(self):
        #Should record a SupplyPointStatus and send out a notification to all the District's sub-facilities.

        contact = register_user(self, "32345", "RandR Tester")

        # submitted successfully
        translation.activate("en")
        sp = SupplyPoint.objects.get(name="TANDAHIMBA")
        contact.supply_point = sp
        contact.save()

        contact = register_user(self, "32346", "Person 1", "d30701", "CHAUME DISP")
        contact = register_user(self, "32347", "Person 2", "d31049", "CHIDEDE DISP")

        script = """
          32345 > nimepokea
          32345 < %(submitted_message)s
        """ % {'submitted_message': _(config.Messages.DELIVERY_CONFIRM_DISTRICT) % {"contact_name":"RandR Tester",
                                                                                    "facility_name":"TANDAHIMBA"}}
        self.runScript(script)

        sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                         status_type="del_dist").order_by("-status_date")[0]

        self.assertEqual(SupplyPointStatusValues.RECEIVED, sps.status_value)
        self.assertEqual(SupplyPointStatusTypes.DELIVERY_DISTRICT, sps.status_type)

        for child in sp.children():
            for c in child.active_contact_set:
                self.assertEqual(Message.objects.filter(contact=c).count(), 2)
                msg = Message.objects.filter(contact=c).order_by("-date")[0]
                self.assertEqual(msg.text, config.Messages.DELIVERY_CONFIRM_CHILDREN % {"district_name":"TANDAHIMBA"})

    def testDeliveryDistrictNotReceived(self):
        contact = register_user(self, "32345", "RandR Tester")

        # submitted successfully
        translation.activate("sw")
        sp = SupplyPoint.objects.get(name="TANDAHIMBA")
        contact.supply_point = sp
        contact.save()

        script = """
          32345 > sijapokea
          32345 < %(submitted_message)s
        """ % {'submitted_message': _(config.Messages.NOT_DELIVERED_CONFIRM)}
        self.runScript(script)

        sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                         status_type="del_dist").order_by("-status_date")[0]

        self.assertEqual(SupplyPointStatusValues.NOT_RECEIVED, sps.status_value)
        self.assertEqual(SupplyPointStatusTypes.DELIVERY_DISTRICT, sps.status_type)


