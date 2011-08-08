from logistics.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics.apps.tanzania.tests.util import register_user

class TestYes(TanzaniaTestScriptBase):
    
    def testYes(self):
        contact = register_user(self, "778", "someone")
        script = """
          778 > ndio
          778 < Kama umetuma R&R fomu yako jibu 'nimetuma', kama umepokea vifaa jibu 'nimepokea'
        """
        self.runScript(script)