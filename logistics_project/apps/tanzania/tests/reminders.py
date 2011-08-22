from logistics_project.apps.tanzania.reminders import stockonhand , delivery
from logistics_project.apps.tanzania.tests.util import register_user
from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.config import SupplyPointCodes
from logistics.models import SupplyPoint, ProductReport, SupplyPointGroup
from rapidsms.models import Contact
from datetime import datetime 
from logistics_project.apps.tanzania.models import DeliveryGroups

class TestStockOnHandReminders(TanzaniaTestScriptBase):
    
    def setUp(self):
        super(TestStockOnHandReminders, self).setUp()
        Contact.objects.all().delete()
        ProductReport.objects.all().delete()
        self.contact = register_user(self, "778", "someone")
        
    def testBasicList(self):
        people = list(stockonhand.get_people(datetime.utcnow()))
        self.assertEqual(1, len(people))
        for person in people:
            self.assertEqual(self.contact, person)
        
    def testDistrictExclusion(self):
        old_sp = self.contact.supply_point
        self.contact.supply_point = SupplyPoint.objects.exclude\
                    (type__code=SupplyPointCodes.FACILITY)[0]
        self.contact.save()
        self.assertEqual(0, len(list(stockonhand.get_people(datetime.utcnow()))))
        self.contact.supply_point = old_sp
        self.contact.save()
        self.assertEqual(1, len(list(stockonhand.get_people(datetime.utcnow()))))
        
    def testReportExclusion(self):
        now = datetime.utcnow()
        self.assertEqual(1, len(list(stockonhand.get_people(now))))
        script = """
            778 > Hmk Id 400 Dp 569 Ip 678
        """
        self.runScript(script)
        self.assertEqual(0, len(list(stockonhand.get_people(now))))
        self.assertEqual(1, len(list(stockonhand.get_people(datetime.utcnow()))))
        

class TestDeliveryReminder(TanzaniaTestScriptBase):
    
    def setUp(self):
        super(TestDeliveryReminder, self).setUp()
        Contact.objects.all().delete()
        ProductReport.objects.all().delete()
        self.contact = register_user(self, "778", "someone")
        sp = self.contact.supply_point
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups.current_delivering_group()),)
        sp.save()
        
    def testGroupExclusion(self):
        people = list(delivery.get_facility_people(datetime.utcnow()))
        self.assertEqual(1, len(people))
        for person in people:
            self.assertEqual(self.contact, person)
        
        sp = self.contact.supply_point
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups.current_submitting_group()),)
        sp.save()
        people = list(delivery.get_facility_people(datetime.utcnow()))
        self.assertEqual(0, len(people))
        
        sp = self.contact.supply_point
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups.current_processing_group()),)
        sp.save()
        people = list(delivery.get_facility_people(datetime.utcnow()))
        self.assertEqual(0, len(people))
        
    def testReportExclusion(self):
        now = datetime.utcnow()
        self.assertEqual(1, len(list(delivery.get_facility_people(now))))
        
        script = """
            778 > nimepokea
        """
        self.runScript(script)
        self.assertEqual(0, len(list(delivery.get_facility_people(now))))
        self.assertEqual(1, len(list(delivery.get_facility_people(datetime.utcnow()))))
        
        
    