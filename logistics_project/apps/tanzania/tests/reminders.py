from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from dimagi.utils.dates import get_business_day_of_month
from datetime import date

class TestBusinessDays(TanzaniaTestScriptBase):
        
    def testBusinessDays(self):
        # normal
        self.assertEqual(date(2011, 8, 1), get_business_day_of_month(2011, 8, 1))
        self.assertEqual(date(2011, 8, 2), get_business_day_of_month(2011, 8, 2))
        self.assertEqual(date(2011, 8, 3), get_business_day_of_month(2011, 8, 3))
        self.assertEqual(date(2011, 8, 4), get_business_day_of_month(2011, 8, 4))
        self.assertEqual(date(2011, 8, 5), get_business_day_of_month(2011, 8, 5))
        self.assertEqual(date(2011, 8, 8), get_business_day_of_month(2011, 8, 6))
        
        # negative
        self.assertEqual(date(2011, 8, 31), get_business_day_of_month(2011, 8, -1))
        self.assertEqual(date(2011, 8, 26), get_business_day_of_month(2011, 8, -4))
        
        # random
        self.assertEqual(date(2011, 9, 1), get_business_day_of_month(2011, 9, 1))
        self.assertEqual(date(2011, 10, 3), get_business_day_of_month(2011, 10, 1))
        self.assertEqual(date(2012, 2, 7), get_business_day_of_month(2012, 2, 5))
        
        # leap year
        self.assertEqual(date(2012, 2, 29), get_business_day_of_month(2012, 2, -1))
        