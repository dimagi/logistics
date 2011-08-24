from logistics_project.apps.tanzania.reminders import reports
from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from rapidsms.models import Contact
from logistics.models import ProductReport, SupplyPoint, SupplyPointGroup
from logistics_project.apps.tanzania.tests.util import register_user
from logistics_project.apps.tanzania.config import SupplyPointCodes
from logistics_project.apps.tanzania.models import DeliveryGroups

class TestReportGroups(TanzaniaTestScriptBase):

    def setUp(self):
        super(TestReportGroups, self).setUp()
        Contact.objects.all().delete()
        ProductReport.objects.all().delete()

        # district contact
        self.contact = register_user(self, "778", "someone")
        sp = SupplyPoint.objects.get(name="TANDAHIMBA")
        self.contact.supply_point = sp
        self.contact.save()

    def testBasicList(self):
        people = list(reports.get_district_people())
        self.assertEqual(1, len(people))
        for person in people:
            self.assertEqual(self.contact, person)

    def testDistrictExclusion(self):
        old_sp = self.contact.supply_point
        self.contact.supply_point = SupplyPoint.objects.exclude\
                    (type__code=SupplyPointCodes.DISTRICT)[0]
        self.contact.save()
        self.assertEqual(0, len(list(reports.get_district_people())))
        self.contact.supply_point = old_sp
        self.contact.save()
        self.assertEqual(1, len(list(reports.get_district_people())))

class TestRandRSummary(TanzaniaTestScriptBase):

    def setUp(self):
        super(TestRandRSummary, self).setUp()
        Contact.objects.all().delete()
        ProductReport.objects.all().delete()

        self.district_contact = register_user(self, "777", "someone")
        sp = SupplyPoint.objects.get(name="TEST DISTRICT")
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups().current_submitting_group()),)
        self.district_contact.supply_point = sp
        self.district_contact.save()
        
        self.facility_contact = register_user(self, "778", "someone")
        self.assertEqual(self.facility_contact.supply_point.supplied_by,
                         self.district_contact.supply_point)
    
    def testBasicReportNoResponses(self):
        
        sp = self.facility_contact.supply_point
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups().current_submitting_group()),)
        sp.save()
        submitting = SupplyPoint.objects.filter\
            (type__code=SupplyPointCodes.FACILITY,
             groups__code=DeliveryGroups().current_submitting_group()).count()

        result = reports.construct_randr_summary(self.district_contact.supply_point)
        self.assertEqual(submitting, result["total"])
        self.assertEqual(submitting, result["not_responding"])
        self.assertEqual(0, result["not_submitted"])
        self.assertEqual(0, result["submitted"])

    def testBasicReportOneResponder(self):
        sp = self.facility_contact.supply_point
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups().current_submitting_group()),)
        sp.save()

        submitting = SupplyPoint.objects.filter\
            (type__code=SupplyPointCodes.FACILITY,
             groups__code=DeliveryGroups().current_submitting_group()).count()

        script = """
            778 > nimetuma
        """
        self.runScript(script)
        result = reports.construct_randr_summary(self.district_contact.supply_point)

        self.assertEqual(submitting, result["total"])
        self.assertEqual(submitting - 1, result["not_responding"])
        self.assertEqual(0, result["not_submitted"])
        self.assertEqual(1, result["submitted"])

    def testBasicReportMultipleResponders(self):
        contact1 = register_user(self, "778", "Test User1", "d10001", "VETA 1")
        contact2 = register_user(self, "779", "Test User2", "d10002", "VETA 2")
        contact3 = register_user(self, "780", "Test User3", "d10003", "VETA 3")

        for sp in [contact1.supply_point, contact2.supply_point, contact3.supply_point]:
            sp.groups = (SupplyPointGroup.objects.get\
                         (code=DeliveryGroups().current_submitting_group()),)
            sp.save()

        submitting = SupplyPoint.objects.filter\
            (type__code=SupplyPointCodes.FACILITY,
             groups__code=DeliveryGroups().current_submitting_group()).count()

        script = """
            778 > nimetuma
        """
        self.runScript(script)
        result = reports.construct_randr_summary(sp.supplied_by)

        self.assertEqual(submitting, result["total"])
        self.assertEqual(submitting-1, result["not_responding"])
        self.assertEqual(0, result["not_submitted"])
        self.assertEqual(1, result["submitted"])

        script = """
            779 > nimetuma
        """
        self.runScript(script)
        result = reports.construct_randr_summary(sp.supplied_by)

        self.assertEqual(submitting, result["total"])
        self.assertEqual(submitting-2, result["not_responding"])
        self.assertEqual(0, result["not_submitted"])
        self.assertEqual(2, result["submitted"])

        script = """
            780 > sijatuma
        """
        self.runScript(script)
        result = reports.construct_randr_summary(sp.supplied_by)

        self.assertEqual(submitting, result["total"])
        self.assertEqual(submitting-3, result["not_responding"])
        self.assertEqual(1, result["not_submitted"])
        self.assertEqual(2, result["submitted"])