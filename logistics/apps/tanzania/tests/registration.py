from logistics.apps.malawi.tests.base import OutputtingTestScript
import os

class TestRegister(OutputtingTestScript):
    
    output_directory = os.path.join(os.path.dirname(__file__), "testscripts")
    
    def testRegister(self):

        script = """
          743 > Register Alfred Mchau d10001
          743 < Asante kwa kujisajili katika VETA 1, d10001, Alfred Mchau
        """
        