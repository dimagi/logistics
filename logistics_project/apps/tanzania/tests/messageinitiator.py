from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user
from django.utils.translation import ugettext as _
from logistics.util import config
from django.utils import translation
from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message
from logistics.models import SupplyPoint, Product
from logistics_project.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues

class TestMessageInitiator(TanzaniaTestScriptBase):

    def setUp(self):
        super(TestMessageInitiator, self).setUp()
        Contact.objects.all().delete()
        Message.objects.all().delete()

    def tearDown(self):
        super(TestMessageInitiator, self).tearDown()

    def testMessageInitiatorHelp(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone", "d10001")

        script = """
            778 > test
            778 < %(test_help)s
            """ % {"test_help": _(config.Messages.TEST_HANDLER_HELP)}
        self.runScript(script)

    def testMessageInitiatorLossedAdjustments(self):
        translation.activate("sw")
        contact = register_user(self, "32000", "Trainer", )
        contact = register_user(self, "32347", "Person 1", "d31049", "CHIDEDE DISP")
        contact = register_user(self, "32348", "Person 2", "d31049", "CHIDEDE DISP")
        contact = register_user(self, "32349", "Person 3", "d31049", "CHIDEDE DISP")

        script = """
            32000 > test la d31049
            32000 < %(test_handler_confirm)s
            32347 < %(response)s
            32348 < %(response)s
            32349 < %(response)s
            """ % {"test_handler_confirm":_(config.Messages.TEST_HANDLER_CONFIRM),
                   "response":_(config.Messages.LOSS_ADJUST_HELP)}
        self.runScript(script)

        sp = SupplyPoint.objects.get(code="D31049")
        sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                         status_type="la_fac").order_by("-status_date")[0]

        self.assertEqual(SupplyPointStatusValues.REMINDER_SENT, sps.status_value)
        self.assertEqual(SupplyPointStatusTypes.LOSS_ADJUSTMENT_FACILITY, sps.status_type)

    def testMessageInitiatorForward(self):
        translation.activate("sw")
        contact = register_user(self, "32000", "Trainer", )
        contact = register_user(self, "32347", "Person 1", "d31049", "CHIDEDE DISP")
        contact = register_user(self, "32348", "Person 2", "d31049", "CHIDEDE DISP")
        contact = register_user(self, "32349", "Person 3", "d31049", "CHIDEDE DISP")

        script = """
            32000 > test fw d31049 %(test_message)s
            32000 < %(test_handler_confirm)s
            32347 < %(test_message)s
            32348 < %(test_message)s
            32349 < %(test_message)s
            """ % {"test_handler_confirm":_(config.Messages.TEST_HANDLER_CONFIRM),
                   "test_message":"this is a test message"}
        self.runScript(script)

    def testMessageInitiatorStockInquiryIndividualLocation(self):
        translation.activate("sw")
        contact = register_user(self, "32000", "Trainer", )
        contact = register_user(self, "32347", "Person 1", "d31049", "CHIDEDE DISP")
        contact = register_user(self, "32348", "Person 2", "d31049", "CHIDEDE DISP")
        contact = register_user(self, "32349", "Person 3", "d31049", "CHIDEDE DISP")

        p = Product.objects.get(sms_code__iexact="id")
        p.product_code = 'm11111'
        p.save()

        sp = SupplyPoint.objects.get(name="TANDAHIMBA")
        sp.code = "D10101"
        sp.save()

        translation.activate("sw")

        script = """
            32000 > test si d31049 m11112
            32000 < %(invalid_code_message)s 
            32000 > test si d31049 m11111
            32000 < %(test_handler_confirm)s
            32347 < %(response)s
            32348 < %(response)s
            32349 < %(response)s
            32000 > test si d10101 m11111
            32000 < %(location_error)s
            """ % {"test_handler_confirm":_(config.Messages.TEST_HANDLER_CONFIRM),
                   "response":_(config.Messages.STOCK_INQUIRY_MESSAGE) % {"product_name":p.name,
                                                                          "msd_code":p.product_code},
                   "invalid_code_message":_(config.Messages.INVALID_PRODUCT_CODE) % {"product_code":"m11112"},
                   "location_error":_(config.Messages.STOCK_INQUIRY_NOT_A_FACILITY_ERROR) % {"location_name":"changeme",
                                                                                             "location_type":"changeme"}}
        self.runScript(script)

    def testMessageInitiatorStockInquiryRecursive(self):
        raise Exception("This test hasn't been implemented yet")

    def testMessageInitiatorBadCode(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone", "d10001")

        script = """
            778 > test la d5000000
            778 < %(test_bad_code)s
            """ % {"test_bad_code": _(config.Messages.TEST_HANDLER_BAD_CODE) % {"code":"D5000000"}}
        self.runScript(script)

    def testMessageInitiatorRandRFacility(self):
        translation.activate("sw")
        register_user(self, "32000", "Trainer", )
        register_user(self, "32347", "Person 1", "d31049", "CHIDEDE DISP")
        register_user(self, "32348", "Person 2", "d31049", "CHIDEDE DISP")
        register_user(self, "32349", "Person 3", "d31049", "CHIDEDE DISP")

        script = """
            32000 > test randr d31049
            32000 < %(test_handler_confirm)s
            32347 < %(response)s
            32348 < %(response)s
            32349 < %(response)s
            """ % {"test_handler_confirm":_(config.Messages.TEST_HANDLER_CONFIRM),
                   "response":_(config.Messages.SUBMITTED_REMINDER_FACILITY)}
        self.runScript(script)

        sp = SupplyPoint.objects.get(code="D31049")
        sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                         status_type="rr_fac").order_by("-status_date")[0]

        self.assertEqual(SupplyPointStatusValues.REMINDER_SENT, sps.status_value)
        self.assertEqual(SupplyPointStatusTypes.R_AND_R_FACILITY, sps.status_type)

    def testMessageInitiatorRandRDistrict(self):
        translation.activate("sw")

        contact = register_user(self, "32000", "Trainer", )

        sp = SupplyPoint.objects.get(name="TANDAHIMBA")
        sp.code = "D10101"
        sp.save()

        for contact_id in ["+255714774041","+255714774042","+255714774043"]:
            register_user(self, contact_id, "Person %s" % contact_id, "d10101", "TANDAHIMBA")

        script = """
            32000 > test randr d10101
            32000 < %(test_handler_confirm)s
            +255714774041 < %(response)s
            +255714774042 < %(response)s
            +255714774043 < %(response)s
            """ % {"test_handler_confirm":_(config.Messages.TEST_HANDLER_CONFIRM),
                   "response":_(config.Messages.SUBMITTED_REMINDER_DISTRICT)}
        self.runScript(script)

        sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                         status_type="rr_dist").order_by("-status_date")[0]

        self.assertEqual(SupplyPointStatusValues.REMINDER_SENT, sps.status_value)
        self.assertEqual(SupplyPointStatusTypes.R_AND_R_DISTRICT, sps.status_type)

    def testMessageInitiatorDeliveryFacility(self):
        translation.activate("sw")
        register_user(self, "+255714700000", "Trainer", )
        register_user(self, "+255714700001", "Person 1", "d31049", "CHIDEDE DISP")
        register_user(self, "+255714700002", "Person 2", "d31049", "CHIDEDE DISP")
        register_user(self, "+255714700003", "Person 3", "d31049", "CHIDEDE DISP")

        script = """
            +255714700000 > test delivery d31049
            +255714700000 < %(test_handler_confirm)s
            +255714700001 < %(response)s
            +255714700002 < %(response)s
            +255714700003 < %(response)s
            """ % {"test_handler_confirm":_(config.Messages.TEST_HANDLER_CONFIRM),
                   "response":_(config.Messages.DELIVERY_REMINDER_FACILITY)}
        self.runScript(script)

        sp = SupplyPoint.objects.get(code="D31049")
        sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                         status_type="del_fac").order_by("-status_date")[0]

        self.assertEqual(SupplyPointStatusValues.REMINDER_SENT, sps.status_value)
        self.assertEqual(SupplyPointStatusTypes.DELIVERY_FACILITY, sps.status_type)

    def testMessageInitiatorDeliveryDistrict(self):
        translation.activate("sw")

        contact = register_user(self, "32000", "Trainer", )

        sp = SupplyPoint.objects.get(name="TANDAHIMBA")
        sp.code = "D10101"
        sp.save()

        for contact_id in ["+255714774041","+255714774042","+255714774043"]:
            register_user(self, contact_id, "Person %s" % contact_id, "d10101", "TANDAHIMBA")

        script = """
            32000 > test delivery d10101
            32000 < %(test_handler_confirm)s
            +255714774041 < %(response)s
            +255714774042 < %(response)s
            +255714774043 < %(response)s
            """ % {"test_handler_confirm":_(config.Messages.TEST_HANDLER_CONFIRM),
                   "response":_(config.Messages.DELIVERY_REMINDER_DISTRICT)}
        self.runScript(script)

        sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                         status_type="del_dist").order_by("-status_date")[0]

        self.assertEqual(SupplyPointStatusValues.REMINDER_SENT, sps.status_value)
        self.assertEqual(SupplyPointStatusTypes.DELIVERY_DISTRICT, sps.status_type)

    def testMessageInitiatorLateDeliveryReportDistrict(self):
        translation.activate("sw")

        register_user(self, "32000", "Trainer", )

        sp = SupplyPoint.objects.get(name="TANDAHIMBA")
        sp.code = "D10101"
        sp.save()

        for contact_id in ["+255714774041","+255714774042","+255714774043"]:
            register_user(self, contact_id, "Person %s" % contact_id, "d10101", "TANDAHIMBA")

        script = """
            32000 > test latedelivery d10101
            32000 < %(test_handler_confirm)s
            +255714774041 < %(response)s
            +255714774042 < %(response)s
            +255714774043 < %(response)s
            """ % {"test_handler_confirm":_(config.Messages.TEST_HANDLER_CONFIRM),
                   "response":_(config.Messages.DELIVERY_LATE_DISTRICT) % {"group_name":"changeme",
                                                                           "group_total":1,
                                                                           "not_responded_count":2,
                                                                           "not_received_count":3}}
        self.runScript(script)

    def testMessageInitiatorSOHFacility(self):
        translation.activate("sw")
        register_user(self, "32000", "Trainer", )
        register_user(self, "32347", "Person 1", "d31049", "CHIDEDE DISP")
        register_user(self, "32348", "Person 2", "d31049", "CHIDEDE DISP")
        register_user(self, "32349", "Person 3", "d31049", "CHIDEDE DISP")

        script = """
            32000 > test soh d31049
            32000 < %(test_handler_confirm)s
            32347 < %(response)s
            32348 < %(response)s
            32349 < %(response)s
            32000 > test hmk d31049
            32000 < %(test_handler_confirm)s
            32347 < %(response)s
            32348 < %(response)s
            32349 < %(response)s
            """ % {"test_handler_confirm":_(config.Messages.TEST_HANDLER_CONFIRM),
                   "response":_(config.Messages.SOH_HELP_MESSAGE)}
        self.runScript(script)

        sp = SupplyPoint.objects.get(code="D31049")
        sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                         status_type="soh_fac").order_by("-status_date")[0]

        self.assertEqual(SupplyPointStatusValues.REMINDER_SENT, sps.status_value)
        self.assertEqual(SupplyPointStatusTypes.SOH_FACILITY, sps.status_type)


    def testMessageInitiatorSOHFacility(self):
        translation.activate("sw")
        register_user(self, "32000", "Trainer", )
        register_user(self, "32347", "Person 1", "d31049", "CHIDEDE DISP")
        register_user(self, "32348", "Person 2", "d31049", "CHIDEDE DISP")
        register_user(self, "32349", "Person 3", "d31049", "CHIDEDE DISP")

        script = """
            32000 > test supervision d31049
            32000 < %(test_handler_confirm)s
            32347 < %(response)s
            32348 < %(response)s
            32349 < %(response)s
            """ % {"test_handler_confirm":_(config.Messages.TEST_HANDLER_CONFIRM),
                   "response":_(config.Messages.SUPERVISION_REMINDER)}
        self.runScript(script)

        sp = SupplyPoint.objects.get(code="D31049")
        sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                         status_type="super_fac").order_by("-status_date")[0]

        self.assertEqual(SupplyPointStatusValues.REMINDER_SENT, sps.status_value)
        self.assertEqual(SupplyPointStatusTypes.SUPERVISION_FACILITY, sps.status_type)



