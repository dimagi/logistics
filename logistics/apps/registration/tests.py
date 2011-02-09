import unittest
from rapidsms.tests.scripted import TestScript

class TestRegister(TestScript):

    def testRegister(self):
        a = """
              8005551212 > register
              8005551212 < To register, send register <name> <msd code>. Example: register john dedh
              8005551212 > register stella
              8005551212 < Sorry, I didn't understand. To register, send register <name> <msd code>. Example: register john dedh'
              8005551212 > register stella doesntexist
              8005551212 < Sorry, can't find the location with MSD CODE doesntexist
              8005551212 > register stella dedh
              8005551212 < Thank you for registering at Dangme East District Hospital, dedh, stella
            """
        self.runScript(a)
