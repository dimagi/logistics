from logistics.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics.apps.tanzania.tests.util import register_user

class TestRandR(TanzaniaTestScriptBase):
    
    def testRandR(self):
        contact = register_user(self, "778", "someone")
        
        # submitted successfully
        script = """
          778 > nimatuma
          778 < Asante %(contact_name)s kwa kuwasilisha R & R fomu kwa %(sdp_name)s
        """ % {"contact_name":contact.name, "sdp_name":"changeme"}
        self.runScript(script)
        
        #not submitted
        script = """
          778 > sijatuma
          778 < %(not_submitted_message)s
        """ % {'not_submitted_message': _(config.Messages.NOT_SUBMITTED_CONFIRM) % {"contact_name":contact.name, "sdp_name":"changeme"}}
        self.runScript(script)        