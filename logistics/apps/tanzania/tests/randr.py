from logistics.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics.apps.tanzania.tests.util import register_user
from django.utils.translation import ugettext as _
from logistics.apps.logistics.util import config
from django.utils import translation
from logistics.apps.logistics.models import SupplyPoint
from logistics.apps.tanzania.models import SupplyPointStatus,\
    SupplyPointStatusTypes, SupplyPointStatusValues

class TestRandR(TanzaniaTestScriptBase):
    
    def testRandRSubmitted(self):
        contact = register_user(self, "778", "someone", "d10001")
        
        # submitted successfully
        translation.activate("sw")
        sp = SupplyPoint.objects.get(code="D10001")

        script = """
          778 > nimatuma
          778 < %(submitted_message)s
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