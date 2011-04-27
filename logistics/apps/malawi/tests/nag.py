from rapidsms.tests.scripted import TestScript
from logistics.apps.malawi.nag import get_non_reporting_hsas

class TestNag(TestScript):
    def testNag(self):
        self._setup_users()
        self.assertEqual(1, get_non_reporting_hsas())
        a = """
           16175551000 > soh zi 10 la 15
           16175551000 < Thank you wendy. The health center in charge has been notified and you will receive an alert when supplies are ready.
           16175551001 < wendy needs the following supplies: zi 390, la 705. Respond 'ready 261601' when supplies are ready
        """
        self.runScript(a)
        self.assertEqual(0, get_non_reporting_hsas())


    def _setup_users(self):
        a = """
           16175551000 > register wendy 1 2616
           16175551000 < Congratulations wendy, you have successfully been registered for the Early Warning System. Your facility is Ntaja
           16175551001 > manage sally ic 2616
           16175551001 < Congratulations sally, you have successfully been registered for the Early Warning System. Your facility is Ntaja
        """
        self.runScript(a)
