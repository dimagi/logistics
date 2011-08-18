from logistics_project.apps.tanzania.reminders import stockonhand 
from logistics_project.apps.tanzania.tests.util import register_user
from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.config import SupplyPointCodes
from logistics.models import SupplyPoint, ProductReport
from rapidsms.models import Contact

class TestStockOnHandReminders(TanzaniaTestScriptBase):
    # nothing here yet.    
    def setUp(self):
        super(TestStockOnHandReminders, self).setUp()
        Contact.objects.all().delete()
        ProductReport.objects.all().delete()
        self.contact = register_user(self, "778", "someone")
        
        
        
    def testBasicList(self):
        people = list(stockonhand.get_people())
        self.assertEqual(1, len(people))
        for person in people:
            self.assertEqual(self.contact, person)
        
    def testDistrictExclusion(self):
        old_sp = self.contact.supply_point
        self.contact.supply_point = SupplyPoint.objects.exclude\
                    (type__code=SupplyPointCodes.FACILITY)[0]
        self.contact.save()
        self.assertEqual(0, len(list(stockonhand.get_people())))
        self.contact.supply_point = old_sp
        self.contact.save()
        self.assertEqual(1, len(list(stockonhand.get_people())))
        
    def testReportExclusion(self):
        self.assertEqual(1, len(list(stockonhand.get_people())))
        script = """
            778 > Hmk Id 400 Dp 569 Ip 678
        """
        self.runScript(script)
        self.assertEqual(0, len(list(stockonhand.get_people())))