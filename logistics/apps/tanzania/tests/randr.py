from logistics.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics.apps.tanzania.tests.util import register_user

class TestRandR(TanzaniaTestScriptBase):
    
    def testRandR(self):
        contact = register_user(self, "778", "someone")
        script = """
          778 > nimatuma
          778 < Asante %(contact_name)s kwa kuwasilisha R & R fomu kwa %(sdp_name)s
        """ % {"contact_name":contact.name, "sdp_name":"changeme"}
        self.runScript(script)