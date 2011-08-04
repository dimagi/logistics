import os
from logistics.apps.tanzania.tests.base import TanzaniaTestScriptBase

class TestHelp(TanzaniaTestScriptBase):
    
    output_directory = os.path.join(os.path.dirname(__file__), "testscripts")
    
    def testHelp(self):

#        English
#        script = """
#          743 > help
#          743 < To register, send register <name> <msd code>. Example: register 'john patel d34002'
#        """

#        Swahili
        script = """
          743 > help
          743 < Haujasajiliwa,Tafadhali jisajili kwanza kabla ya kupata huduma,Kusajili andika 'sajili<nafasi><jina lako><nafasi><msd code>'. Mfano 'sajili Peter Juma d34002'
        """
        self.runScript(script)