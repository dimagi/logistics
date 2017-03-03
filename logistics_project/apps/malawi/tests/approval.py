from django.conf import settings
from logistics_project.apps.malawi import loader
from rapidsms.models import Contact
from logistics_project.apps.malawi.tests.base import MalawiTestBase
from logistics_project.apps.malawi.tests.util import create_manager, create_hsa,\
    report_stock
__author__ = 'ternus'
from logistics.models import Location, SupplyPoint
from logistics.util import config

class TestApproval(MalawiTestBase):

    def setUp(self):
        super(TestApproval, self).setUp()
        settings.LOGISTICS_APPROVAL_REQUIRED = True

    def testBasicApprovalWorkflow(self):
        a = """
              +8005551200 > manage manager sh 2616
              +8005551200 < %(manage)s
              +8005551212 > reg stella 1 2616
              +8005551212 < %(approval_waiting)s
              +8005551200 < %(approval_request)s
              +8005551212 > add zi co la
              +8005551212 < %(approval_required)s

            """ % {'manage': config.Messages.REGISTRATION_CONFIRM % {'contact_name': 'manager',
                                                                     'sp_name': 'Ntaja',
                                                                     'role': 'hsa supervisor'},
                   'approval_waiting': config.Messages.APPROVAL_WAITING % {'hsa': 'stella'},
                   'approval_request': config.Messages.APPROVAL_REQUEST % {'hsa': 'stella',
                                                                           'code': '261601'},
                   'approval_required': config.Messages.APPROVAL_REQUIRED
                   }
        self.runScript(a)
        loc = Location.objects.get(code="261601")
        sp = SupplyPoint.objects.get(code="261601")
        c = Contact.objects.get(supply_point=sp)
        self.assertFalse(c.is_approved)

        a = """
              +8005551200 > approve 261601
              +8005551200 < %(approval_supervisor)s
              +8005551212 < %(approval_hsa)s
              +8005551212 > add zi co la
              +8005551212 > Thank you, you now supply: co la zi
            """ % {'approval_supervisor': config.Messages.APPROVAL_SUPERVISOR % {'hsa': 'stella'},
                   'approval_hsa': config.Messages.APPROVAL_HSA % {'hsa':'stella'}}
        self.runScript(a)
        c = Contact.objects.get(supply_point=sp)
        self.assertTrue(c.is_approved)

    def testApprovalNoSupervisor(self):
        """
        This is exactly the same as the test in register.py.  It should succeed, since no HSA
        Supervisor has been defined for this facility.
        """
        a = """
              +8005551212 > reg
              +8005551212 < %(help_message)s
              +8005551212 > reg stella
              +8005551212 < %(help_message)s
              +8005551212 > reg stella 1 doesntexist
              +8005551212 < %(bad_loc)s
              +8005551212 > reg stella 1 2616
              +8005551212 < %(confirm)s
            """ % {'register_message':config.Messages.REGISTER_MESSAGE, 'help_message':config.Messages.HSA_HELP,
                   'bad_loc': config.Messages.UNKNOWN_LOCATION % {"code": "doesntexist"},
                   "confirm": config.Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                               "role": "hsa",
                                                               "contact_name": "stella"}}
        self.runScript(a)
        loc = Location.objects.get(code="261601")
        sp = SupplyPoint.objects.get(code="261601")
        self.assertEqual(sp.location, loc)


