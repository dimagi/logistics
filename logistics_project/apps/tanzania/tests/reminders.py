from logistics_project.apps.tanzania.reminders import stockonhand , delivery,\
    randr, reports
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
                     (code=DeliveryGroups().current_delivering_group()),)
        sp.save()

    def testGroupExclusion(self):
        people = list(delivery.get_facility_people(datetime.utcnow()))
        self.assertEqual(1, len(people))
        for person in people:
            self.assertEqual(self.contact, person)

        sp = self.contact.supply_point
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups().current_submitting_group()),)
        sp.save()
        people = list(delivery.get_facility_people(datetime.utcnow()))
        self.assertEqual(0, len(people))

        sp = self.contact.supply_point
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups().current_processing_group()),)
        sp.save()
        people = list(delivery.get_facility_people(datetime.utcnow()))
        self.assertEqual(0, len(people))

    def testReportExclusion(self):
        now = datetime.utcnow()
        self.assertEqual(1, len(list(delivery.get_facility_people(now))))

        # reports for a different type shouldn't update status
        script = """
            778 > nimetuma
        """
        self.assertEqual(1, len(list(delivery.get_facility_people(now))))

        script = """
            778 > nimepokea
        """
        self.runScript(script)
        self.assertEqual(0, len(list(delivery.get_facility_people(now))))
        self.assertEqual(1, len(list(delivery.get_facility_people(datetime.utcnow()))))


class TestRandRReminder(TanzaniaTestScriptBase):

    def setUp(self):
        super(TestRandRReminder, self).setUp()
        Contact.objects.all().delete()
        ProductReport.objects.all().delete()
        self.contact = register_user(self, "778", "someone")
        sp = self.contact.supply_point
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups().current_submitting_group()),)
        sp.save()

    def testGroupExclusion(self):
        people = list(randr.get_facility_people(datetime.utcnow()))
        self.assertEqual(1, len(people))
        for person in people:
            self.assertEqual(self.contact, person)

        sp = self.contact.supply_point
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups().current_delivering_group()),)
        sp.save()
        self.assertEqual(0, len(list(randr.get_facility_people(datetime.utcnow()))))

        sp = self.contact.supply_point
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups().current_processing_group()),)
        sp.save()
        self.assertEqual(0, len(list(randr.get_facility_people(datetime.utcnow()))))

    def testReportExclusion(self):
        now = datetime.utcnow()
        self.assertEqual(1, len(list(randr.get_facility_people(now))))

        # reports for a different type shouldn't update status
        script = """
            778 > nimepokea
        """
        self.runScript(script)
        self.assertEqual(1, len(list(randr.get_facility_people(now))))

        script = """
            778 > nimetuma
        """
        self.runScript(script)
        self.assertEqual(0, len(list(randr.get_facility_people(now))))
        self.assertEqual(1, len(list(randr.get_facility_people(datetime.utcnow()))))

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
                    (type__code=SupplyPointCodes.FACILITY)[0]
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

        #district contact
        self.contact = register_user(self, "778", "someone")
        sp = SupplyPoint.objects.get(name="TANDAHIMBA")
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups().current_submitting_group()),)
        self.contact.supply_point = sp
        self.contact.save()

    def testBasicReportNoResponses(self):
        self.contact = register_user(self, "778", "someone")
        sp = self.contact.supply_point
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups().current_submitting_group()),)
        sp.save()
        submitting = SupplyPoint.objects.filter\
            (type__code=SupplyPointCodes.FACILITY,
             groups__code=DeliveryGroups().current_submitting_group()).count()

        result = reports.construct_randr_summary(self.contact.supply_point.supplied_by)

        self.assertEqual(submitting, result["total"])
        self.assertEqual(submitting, result["not_responding"])
        self.assertEqual(0, result["not_submitted"])
        self.assertEqual(0, result["submitted"])

    def testBasicReportOneResponder(self):
        self.contact = register_user(self, "778", "someone")
        sp = self.contact.supply_point
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
        result = reports.construct_randr_summary(self.contact.supply_point.supplied_by)

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

        self.assertEqual(3, result["total"])
        self.assertEqual(2, result["not_responding"])
        self.assertEqual(0, result["not_submitted"])
        self.assertEqual(1, result["submitted"])

        script = """
            779 > nimetuma
        """
        self.runScript(script)
        result = reports.construct_randr_summary(sp.supplied_by)

        self.assertEqual(3, result["total"])
        self.assertEqual(1, result["not_responding"])
        self.assertEqual(0, result["not_submitted"])
        self.assertEqual(2, result["submitted"])

        script = """
            780 > sijatuma
        """
        self.runScript(script)
        result = reports.construct_randr_summary(sp.supplied_by)

        self.assertEqual(3, result["total"])
        self.assertEqual(0, result["not_responding"])
        self.assertEqual(1, result["not_submitted"])
        self.assertEqual(2, result["submitted"])