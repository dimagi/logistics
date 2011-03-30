from rapidsms.tests.scripted import TestScript
from logistics.apps.reports.tasks import *

class TestReports (TestScript):
    def testDailyEmailReports(self):
        daily_reports()

    def testWeeklyEmailReports(self):
        weekly_reports()
