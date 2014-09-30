from django.utils import translation
from logistics_project.apps.tanzania.models import SupplyPointStatus, SupplyPointStatusTypes, SupplyPointStatusValues
from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user
from logistics.util import config
from django.utils.translation import ugettext as _



class TestTrans(TanzaniaTestScriptBase):
    
    def testTrans(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone")
        script = """
          778 > trans yes
          778 < %s
        """ % _(config.Messages.SOH_CONFIRM)
        self.runScript(script)
        
        script = """
          778 > trans no
          778 < %s
        """ % _(config.Messages.SOH_CONFIRM)
        self.runScript(script)

        self.assertEqual(2, SupplyPointStatus.objects.count())
        status1 = SupplyPointStatus.objects.get(status_type=SupplyPointStatusTypes.TRANS_FACILITY,
                                                status_value=SupplyPointStatusValues.NOT_SUBMITTED)
        status2 = SupplyPointStatus.objects.get(status_type=SupplyPointStatusTypes.TRANS_FACILITY,
                                                status_value=SupplyPointStatusValues.SUBMITTED)
        self.assertEqual(contact.supply_point, status1.supply_point)
        self.assertEqual(contact.supply_point, status2.supply_point)
