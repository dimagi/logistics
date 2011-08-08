from logistics.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics.apps.tanzania.tests.util import register_user

class TestSupervision(TanzaniaTestScriptBase):
    
    def testSupervision(self):
        contact = register_user(self, "778", "someone")
        script = """
          778 > usimamizi ndio
          778 < Asante, umetoa taarifa kuwa 'usimamizi ndiyo'
        """
        self.runScript(script)
        
        script = """
          778 > usimamizi hapana
          778 < Umetoa taarifa kuwa haujafanyiwa usimazi kwa mwezi huu.
        """
        self.runScript(script)        