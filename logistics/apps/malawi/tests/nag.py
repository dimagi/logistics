from datetime import datetime, timedelta
from logistics.apps.logistics.models import NagRecord
from logistics.apps.malawi.nag import get_non_reporting_hsas, nag_hsas, DAYS_BETWEEN_FIRST_AND_SECOND_WARNING, DAYS_BETWEEN_SECOND_AND_THIRD_WARNING
from logistics.apps.malawi.tests.util import create_hsa, create_manager
from rapidsms.tests.scripted import TestScript

class TestNag(TestScript):
    fixtures = ["malawi_products.json"]
    
    def testGetNonReportingHSAs(self):
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

    def testNagHSAs(self):
        hsa = self._setup_users()
        last_month = datetime.utcnow() - timedelta(days=30)
        self.assertEqual(1, len(get_non_reporting_hsas(last_month)))

        nag_hsas(last_month)

        self.assertEqual(1, len(NagRecord.objects.all()))
        nagRecord = NagRecord.objects.all()[0]
        self.assertEqual(hsa, nagRecord.supply_point)
        self.assertEqual(1, nagRecord.warning)

        nagRecord.delete()

        NagRecord(supply_point=hsa, warning=1,
                  report_date=datetime.utcnow()-timedelta(days=DAYS_BETWEEN_FIRST_AND_SECOND_WARNING + 1)).save()

        nag_hsas(last_month)

        self.assertEqual(1, len(NagRecord.objects.all()))
        nagRecord = NagRecord.objects.all()[0]
        self.assertEqual(hsa, nagRecord.supply_point)
        self.assertEqual(2, nagRecord.warning)

        a = """
           16175551000 > soh zi 10 la 15
           16175551000 < Thank you wendy. The health center in charge has been notified and you will receive an alert when supplies are ready.
           16175551001 < wendy needs the following supplies: zi 390, la 705. Respond 'ready 261601' when supplies are ready
        """
        self.runScript(a)
        self.assertEqual(0, len(get_non_reporting_hsas(last_month)))
        self.assertEqual(1, len(get_non_reporting_hsas(datetime.utcnow())))


    def _setup_users(self):
        create_manager(self, "16175551001", "sally")
        return create_hsa(self, "16175551000", "wendy")

        