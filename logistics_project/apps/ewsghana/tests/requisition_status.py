from rapidsms.tests.scripted import TestScript
from logistics_project.apps.ewsghana.tests.util import load_test_data
from logistics.util import config

class TestEquivalents(TestScript):
    def setUp(self):
        TestScript.setUp(self)
        load_test_data()

    def testLowStock(self):
        a = """
              123 > register stella dedh
              123 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
              123 > yes
              123 < %(yes_response)s
            """ % {'yes_response': config.Messages.REQ_SUBMITTED,
                   'no_response': config.Messages.REQ_NOT_SUBMITTED}
        self.runScript(a)

