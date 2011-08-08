from logistics.apps.tanzania.tests.base import TanzaniaTestScriptBase

class TestRegistration(TanzaniaTestScriptBase):
    
    def testRegister(self):
        script = """
          743 > sajili Alfred Mchau d10001
          743 < Asante kwa kujisajili katika VETA 1, d10001, Alfred Mchau
        """
        self.runScript(script)