import os
from logistics.apps.tanzania.tests.base import TanzaniaTestScriptBase

class TestRegister(TanzaniaTestScriptBase):
    
    
    def testRegister(self):

        script = """
          743 > sajili Alfred Mchau d10001
          743 < Asante kwa kujisajili katika Test Facility, d10001, Alfred Mchau
        """
        self.runScript(script)