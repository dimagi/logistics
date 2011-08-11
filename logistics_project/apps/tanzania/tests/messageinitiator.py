from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user
from django.utils.translation import ugettext as _
from logistics.util import config
from django.utils import translation
from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message
from logistics.models import SupplyPoint
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

        for command, response in {'la':config.Messages.LOSS_ADJUST_HELP}.iteritems():
            script = """
                32000 > test %(command)s d31049
                32000 < %(test_handler_confirm)s
                32347 < %(response)s
                32348 < %(response)s
                32349 < %(response)s
                """ % {"test_handler_confirm":_(config.Messages.TEST_HANDLER_CONFIRM),
                       "response":_(response),
                       "command":command}
            self.runScript(script)

            sp = SupplyPoint.objects.get(code="D31049")
            sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                             status_type="la_fac").order_by("-status_date")[0]

            self.assertEqual(SupplyPointStatusValues.REMINDER_SENT, sps.status_value)
            self.assertEqual(SupplyPointStatusTypes.LOSS_ADJUSTMENT_FACILITY, sps.status_type)


    def testMessageInitiatorStockInquiry(self):
        raise Exception("This test hasn't been implemented yet")

    def testMessageInitiatorForwarding(self):
        raise Exception("This test hasn't been implemented yet")

    def testMessageInitiatorBadCode(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone", "d10001")

        script = """
            778 > test la d5000000
            778 < %(test_bad_code)s
            """ % {"test_bad_code": _(config.Messages.TEST_HANDLER_BAD_CODE) % {"code":"D5000000"}}
        self.runScript(script)
