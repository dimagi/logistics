from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user
from django.utils.translation import ugettext as _
from logistics.util import config
from django.utils import translation
from logistics.models import SupplyPoint, Contact
from logistics_project.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues

class TestRandR(TanzaniaTestScriptBase):

    def setUp(self):
        super(TestRandR, self).setUp()
        Contact.objects.all().delete()

    def testRandRSubmittedDistrict(self):
        contact = register_user(self, "22345", "RandR Tester")

        # submitted successfully
        translation.activate("sw")
        sp = SupplyPoint.objects.get(name="TANDAHIMBA")
        contact.supply_point = sp
        contact.save()

        script = """
          22345 > nimetuma
          22345 < %(submitted_message)s
        """ % {'submitted_message': _(config.Messages.SUBMITTED_REMINDER_DISTRICT)}
        self.runScript(script)

        sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                         status_type="rr_dist").order_by("-status_date")[0]

        self.assertEqual(SupplyPointStatusValues.SUBMITTED, sps.status_value)
        self.assertEqual(SupplyPointStatusTypes.R_AND_R_DISTRICT, sps.status_type)

    def testRandRSubmittedDistrictWithAmounts(self):
        raise Exception("This test needs to be implemented")

    def testRandRSubmittedFacility(self):
        contact = register_user(self, "12345", "RandR Tester", "d10001")
        
        # submitted successfully
        translation.activate("en")
        sp = SupplyPoint.objects.get(code="D10001")

        script = """
          12345 > nimetuma
          12345 < %(submitted_message)s
        """ % {'submitted_message': _(config.Messages.SUBMITTED_CONFIRM) % {"contact_name":contact.name,
                                                                                    "sdp_name":sp.name}}
        self.runScript(script)

        sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                         status_type="rr_fac").order_by("-status_date")[0]

        self.assertEqual(SupplyPointStatusValues.SUBMITTED, sps.status_value)
        self.assertEqual(SupplyPointStatusTypes.R_AND_R_FACILITY, sps.status_type)

    def testRandRNotSubmitted(self):
        contact = register_user(self, "778", "someone", "d10001")

        #not submitted
        translation.activate("sw")
        sp = SupplyPoint.objects.get(code="D10001")
        script = """
          778 > sijatuma
          778 < %(not_submitted_message)s
        """ % {'not_submitted_message': _(config.Messages.NOT_SUBMITTED_CONFIRM)}
        self.runScript(script)

        sp = SupplyPoint.objects.get(code="D10001")
        sps = SupplyPointStatus.objects.filter(supply_point=sp,
                                         status_type="rr_fac").order_by("-status_date")[0]

        self.assertEqual(SupplyPointStatusValues.NOT_SUBMITTED, sps.status_value)
        self.assertEqual(SupplyPointStatusTypes.R_AND_R_FACILITY, sps.status_type)