from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user
from rapidsms.models import Contact

class TestStop(TanzaniaTestScriptBase):
    
    def testStop(self):
        contact = register_user(self, "778", "someone")
        script = """
          778 > stop
          778 < Umesitisha kukumbushwa kwenye hii namba. tafadhali tuma 'msaada' kupata maelekezo jinsi ya kujiunga tena
        """
        self.runScript(script)
        contact = Contact.objects.get(name="someone")
        self.assertFalse(contact.is_active)
