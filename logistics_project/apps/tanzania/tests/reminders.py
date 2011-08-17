from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from dimagi.utils.dates import get_business_day_of_month,\
    get_business_day_of_month_after, get_business_day_of_month_before
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
    
    def testBusinessDaysAfter(self):
        # normal
        self.assertEqual(date(2011, 8, 1), get_business_day_of_month_after(2011, 8, 1))
        self.assertEqual(date(2011, 8, 5), get_business_day_of_month_after(2011, 8, 5))
        self.assertEqual(date(2011, 8, 8), get_business_day_of_month_after(2011, 8, 6))
        self.assertEqual(date(2011, 8, 8), get_business_day_of_month_after(2011, 8, 7))
        self.assertEqual(date(2011, 8, 8), get_business_day_of_month_after(2011, 8, 8))
        
        # random 
        self.assertEqual(date(2011, 8, 26), get_business_day_of_month_after(2011, 8, 26))
        self.assertEqual(date(2011, 8, 29), get_business_day_of_month_after(2011, 8, 27))
        self.assertEqual(date(2011, 10, 17), get_business_day_of_month_after(2011, 10, 15))
        self.assertEqual(date(2011, 12, 20), get_business_day_of_month_after(2011, 12, 20))
        
        # fail
        try:
            get_business_day_of_month_after(2011, 12, 31)
            self.fail("previous call should have failed")
        except ValueError: pass
        try:
            get_business_day_of_month_after(2011, 2, 30)
            self.fail("previous call should have failed")
        except ValueError: pass
            
        
    def testBusinessDaysBefore(self):
        self.assertEqual(date(2011, 8, 1), get_business_day_of_month_before(2011, 8, 1))
        self.assertEqual(date(2011, 8, 5), get_business_day_of_month_before(2011, 8, 5))
        self.assertEqual(date(2011, 8, 5), get_business_day_of_month_before(2011, 8, 6))
        self.assertEqual(date(2011, 8, 5), get_business_day_of_month_before(2011, 8, 7))
        self.assertEqual(date(2011, 8, 8), get_business_day_of_month_before(2011, 8, 8))
        
        # random 
        self.assertEqual(date(2011, 8, 26), get_business_day_of_month_before(2011, 8, 26))
        self.assertEqual(date(2011, 8, 26), get_business_day_of_month_before(2011, 8, 27))
        self.assertEqual(date(2011, 8, 29), get_business_day_of_month_before(2011, 8, 29))
        self.assertEqual(date(2011, 10, 14), get_business_day_of_month_before(2011, 10, 15))
        self.assertEqual(date(2011, 12, 20), get_business_day_of_month_before(2011, 12, 20))
        
        
        # fail
        try:
            get_business_day_of_month_before(2011, 10, 1)
            self.fail("previous call should have failed")
        except ValueError: pass
        