from logistics.apps.tanzania.tests.base import TanzaniaTestScriptBase

class TestHelp(TanzaniaTestScriptBase):
    
    def testHelp(self):

#        Swahili
        script = """
          743 > help
          743 < Haujasajiliwa,Tafadhali jisajili kwanza kabla ya kupata huduma,Kusajili andika 'sajili<nafasi><jina lako><nafasi><msd code>'. Mfano 'sajili Peter Juma d34002'
        """
        self.runScript(script)