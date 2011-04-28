from rapidsms.tests.scripted import TestScript
from datetime import datetime, timedelta
from logistics.apps.malawi.nag import get_non_reporting_hsas
from logistics.apps.malawi.tests.util import create_hsa, create_manager

class TestNag(TestScript):
    fixtures = ["malawi_products.json"]
    
    def testNag(self):
        self._setup_users()
        last_month = datetime.utcnow() - timedelta(days=30)
        self.assertEqual(1, len(get_non_reporting_hsas(last_month)))
        a = """
           16175551000 > soh zi 10 la 15
           16175551000 < Thank you wendy. The health center in charge has been notified and you will receive an alert when supplies are ready.
           16175551001 < wendy needs the following supplies: zi 390, la 705. Respond 'ready 261601' when supplies are ready
        """
        self.runScript(a)
        self.assertEqual(0, len(get_non_reporting_hsas(last_month)))
        self.assertEqual(1, len(get_non_reporting_hsas(datetime.utcnow())))


    def _setup_users(self):
        create_hsa(self, "16175551000", "wendy")
        create_manager(self, "16175551001", "sally")
        