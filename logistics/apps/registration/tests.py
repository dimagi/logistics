import unittest
from rapidsms.tests.scripted import TestScript
from logistics.apps.logistics.models import REGISTER_MESSAGE

class TestRegister(TestScript):

    def testRegister(self):
        a = """
              8005551212 > register
              8005551212 < %(register_message)s
              8005551212 > register stella
              8005551212 < Sorry, I didn't understand. To register, send register <name> <facility code>. Example: register john dwdh'
              8005551212 > register stella doesntexist
              8005551212 < Sorry, can't find the location with FACILITY CODE doesntexist
              8005551212 > register stella dwdh
              8005551212 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme West District Hospital
            """ % {'register_message':REGISTER_MESSAGE}
        self.runScript(a)

    def testRegisterTwice(self):
        a = """
              8005551212 > register stella dwdh
              8005551212 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme West District Hospital
              8005551212 > register cynthia dwdh
              8005551212 < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Dangme West District Hospital
            """
        self.runScript(a)
