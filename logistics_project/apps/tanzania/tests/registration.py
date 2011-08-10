from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from django.utils.translation import ugettext as _
from django.utils import translation
from logistics.util import config
from logistics.models import SupplyPoint

class TestRegistration(TanzaniaTestScriptBase):
    
    def testRegister(self):
        translation.activate("sw")
        sp = SupplyPoint.objects.get(code="D10001")
        script = """
          743 > sajili Alfred Mchau d10001
          743 < %(registration_confirm)s
        """ % {"registration_confirm": _(config.Messages.REGISTRATION_CONFIRM) % {"sdp_name": sp.name,
                                                      "msd_code": "d10001" ,
                                                      "contact_name":"Alfred Mchau"}}
        self.runScript(script)