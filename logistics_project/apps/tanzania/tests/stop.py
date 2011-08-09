from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user

class TestStop(TanzaniaTestScriptBase):
    
    def testStop(self):
        contact = register_user(self, "778", "someone")
        script = """
          778 > stop
          778 < Umesitisha kukumbushwa kwenye hii namba. tafadhali tuma 'msaada' kupata maelekezo jinsi ya kujiunga tena
        """
        self.runScript(script)
        self.assertFalse(contact.is_active)
