from logistics_project.apps.tanzania.reminders import reports
from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from rapidsms.models import Contact
from logistics.models import ProductReport, SupplyPoint, SupplyPointGroup
from logistics_project.apps.tanzania.tests.util import register_user
from logistics_project.apps.tanzania.config import SupplyPointCodes
from logistics_project.apps.tanzania.models import DeliveryGroups
from django.utils.translation import ugettext as _
from logistics.util import config
from django.utils import translation

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

class TestReportSummaryBase(TanzaniaTestScriptBase):
    """
    Stub base class for the report tests. Provides some convenience methods
    and does some initial setup of facility and distsrict users and supply
    points.
    """
    
    @property
    def relevant_group(self):
        raise NotImplementedError
    
    @property
    def relevant_count(self):
        return SupplyPoint.objects.filter\
            (type__code=SupplyPointCodes.FACILITY,
             groups__code=self.relevant_group,
             supplied_by=self.district_contact.supply_point).count()
    
    def setUp(self):
        super(TestReportSummaryBase, self).setUp()
        Contact.objects.all().delete()
        ProductReport.objects.all().delete()

        self.district_contact = register_user(self, "777", "someone")
        sp = SupplyPoint.objects.get(name="TEST DISTRICT")
        sp.groups = (SupplyPointGroup.objects.get\
                     (code=DeliveryGroups().current_submitting_group()),)
        self.district_contact.supply_point = sp
        self.district_contact.save()
        
        contact1 = register_user(self, "778", "Test User1", "d10001", "VETA 1")
        contact2 = register_user(self, "779", "Test User2", "d10002", "VETA 2")
        contact3 = register_user(self, "780", "Test User3", "d10003", "VETA 3")
        self.facility_contacts = [contact1, contact2, contact3]
        for contact in self.facility_contacts:
            # make sure parentage is right
            self.assertEqual(contact.supply_point.supplied_by,
                             self.district_contact.supply_point)
            # make sure group is right 
            contact.supply_point.groups = (SupplyPointGroup.objects.get\
                                           (code=self.relevant_group),)
            contact.supply_point.save()
            
    
class TestRandRSummary(TestReportSummaryBase):

    @property
    def relevant_group(self):
        return DeliveryGroups().current_submitting_group()
    
    def testBasicReportNoResponses(self):
        result = reports.construct_randr_summary(self.district_contact.supply_point)
        self.assertEqual(self.relevant_count, result["total"])
        self.assertEqual(self.relevant_count, result["not_responding"])
        self.assertEqual(0, result["not_submitted"])
        self.assertEqual(0, result["submitted"])

    def testPositiveResponses(self):
        script = """
            %(phone)s > nimetuma
        """
        for i, contact in enumerate(self.facility_contacts):
            self.runScript(script % {"phone": contact.default_connection.identity})
            result = reports.construct_randr_summary(self.district_contact.supply_point)
            self.assertEqual(self.relevant_count, result["total"])
            self.assertEqual(self.relevant_count - 1 - i, result["not_responding"])
            self.assertEqual(0, result["not_submitted"])
            self.assertEqual(1 + i, result["submitted"])

    def testNegativeResponses(self):
        script = """
            %(phone)s > sijatuma
        """
        for i, contact in enumerate(self.facility_contacts):
            self.runScript(script % {"phone": contact.default_connection.identity})
            result = reports.construct_randr_summary(self.district_contact.supply_point)
            self.assertEqual(self.relevant_count, result["total"])
            self.assertEqual(self.relevant_count - 1 - i, result["not_responding"])
            self.assertEqual(1 + i, result["not_submitted"])
            self.assertEqual(0, result["submitted"])

    def testOverrides(self):
        self.testPositiveResponses()
        # at this point they should all be positive. But if we send 
        # an additional negative it should override it
        script = """
            %(phone)s > sijatuma
        """
        for i, contact in enumerate(self.facility_contacts):
            self.runScript(script % {"phone": contact.default_connection.identity})
            result = reports.construct_randr_summary(self.district_contact.supply_point)
            self.assertEqual(self.relevant_count, result["total"])
            self.assertEqual(self.relevant_count - 3, result["not_responding"])
            self.assertEqual(1 + i, result["not_submitted"])
            self.assertEqual(self.relevant_count - 1 - i, result["submitted"])

    def testMessageInitiation(self):
        
        translation.activate("sw")

        script = """
            777 > test randr_report TEST DISTRICT
            777 < %(test_handler_confirm)s
            777 < %(report_results)s
        """ % {"test_handler_confirm": _(config.Messages.TEST_HANDLER_CONFIRM),
               "report_results":       _(config.Messages.REMINDER_MONTHLY_RANDR_SUMMARY) %
                                            {"submitted": 0,
                                             "total": 3,
                                             "not_submitted": 0,
                                             "not_responding": 3} }
        self.runScript(script)

        script = """
            778 > nimetuma
            779 > sijatuma
        """
        self.runScript(script)
        
        script = """
            777 > test randr_report TEST DISTRICT
            777 < %(test_handler_confirm)s
            777 < %(report_results)s
        """ % {"test_handler_confirm": _(config.Messages.TEST_HANDLER_CONFIRM),
               "report_results":       _(config.Messages.REMINDER_MONTHLY_RANDR_SUMMARY) %
                                            {"submitted": 1,
                                             "total": 3,
                                             "not_submitted": 1,
                                             "not_responding": 1} }
        self.runScript(script)

class TestDeliverySummary(TestReportSummaryBase):

    @property
    def relevant_group(self):
        return DeliveryGroups().current_delivering_group()
    
    def testBasicReportNoResponses(self):
        result = reports.construct_delivery_summary(self.district_contact.supply_point)
        self.assertEqual(self.relevant_count, result["total"])
        self.assertEqual(self.relevant_count, result["not_responding"])
        self.assertEqual(0, result["not_received"])
        self.assertEqual(0, result["received"])

    def testPositiveResponses(self):
        script = """
            %(phone)s > nimepokea
        """
        not_responding = 0
        not_received = 0
        received = 0

        for i, contact in enumerate(self.facility_contacts):
            self.runScript(script % {"phone": contact.default_connection.identity})
            result = reports.construct_delivery_summary(self.district_contact.supply_point)
            not_responding = result["not_responding"]
            not_received = result["not_received"]
            received = result["received"]
            self.assertEqual(self.relevant_count, result["total"])
            self.assertEqual(self.relevant_count - 1 - i, not_responding)
            self.assertEqual(0, not_received)
            self.assertEqual(1 + i, received)

    def testNegativeResponses(self):
        script = """
            %(phone)s > sijapokea
        """
        for i, contact in enumerate(self.facility_contacts):
            self.runScript(script % {"phone": contact.default_connection.identity})
            result = reports.construct_delivery_summary(self.district_contact.supply_point)
            self.assertEqual(self.relevant_count, result["total"])
            self.assertEqual(self.relevant_count - 1 - i, result["not_responding"])
            self.assertEqual(1 + i, result["not_received"])
            self.assertEqual(0, result["received"])

    def testOverrides(self):
        self.testPositiveResponses()
        # at this point they should all be positive. But if we send 
        # an additional negative it should override it
        script = """
            %(phone)s > sijapokea
        """
        for i, contact in enumerate(self.facility_contacts):
            self.runScript(script % {"phone": contact.default_connection.identity})
            result = reports.construct_delivery_summary(self.district_contact.supply_point)
            self.assertEqual(self.relevant_count, result["total"])
            self.assertEqual(self.relevant_count - 3, result["not_responding"])
            self.assertEqual(1 + i, result["not_received"])
            self.assertEqual(self.relevant_count - 1 - i, result["received"])

    def testMessageInitiation(self):
        translation.activate("sw")

        script = """
            777 > test delivery_report TEST DISTRICT
            777 < %(test_handler_confirm)s
            777 < %(report_results)s
        """ % {"test_handler_confirm": _(config.Messages.TEST_HANDLER_CONFIRM),
               "report_results":       _(config.Messages.REMINDER_MONTHLY_DELIVERY_SUMMARY) %
                                            {"received": 0,
                                             "total": 3,
                                             "not_received": 0,
                                             "not_responding": 3} }
        self.runScript(script)
        
        script = """
            778 > nimepokea
            779 > sijapokea
        """
        self.runScript(script)
        
        script = """
            777 > test delivery_report TEST DISTRICT
            777 < %(test_handler_confirm)s
            777 < %(report_results)s
        """ % {"test_handler_confirm": _(config.Messages.TEST_HANDLER_CONFIRM),
               "report_results":       _(config.Messages.REMINDER_MONTHLY_DELIVERY_SUMMARY) %
                                            {"received": 1,
                                             "total": 3,
                                             "not_received": 1,
                                             "not_responding": 1} }
        self.runScript(script)

class TestSoHSummary(TestReportSummaryBase):

    @property
    def relevant_group(self):
        # this doesn't really matter since it's relevant every month
        return DeliveryGroups().current_delivering_group()
    
    def testBasicReportNoResponses(self):
        result = reports.construct_soh_summary(self.district_contact.supply_point)
        self.assertEqual(self.relevant_count, result["total"])
        self.assertEqual(self.relevant_count, result["not_responding"])
        self.assertEqual(0, result["submitted"])
        
    def testPositiveResponses(self):
        script = """
            %(phone)s > Hmk Id 400 Dp 569 Ip 678
        """
        for i, contact in enumerate(self.facility_contacts):
            self.runScript(script % {"phone": contact.default_connection.identity})
            result = reports.construct_soh_summary(self.district_contact.supply_point)
            self.assertEqual(self.relevant_count, result["total"])
            self.assertEqual(self.relevant_count - 1 - i, result["not_responding"])
            self.assertEqual(1 + i, result["submitted"])

    def testMessageInitiation(self):
        translation.activate("sw")

        script = """
            777 > test soh_report TEST DISTRICT
            777 < %(test_handler_confirm)s
            777 < %(report_results)s
        """ % {"test_handler_confirm": _(config.Messages.TEST_HANDLER_CONFIRM),
               "report_results":       _(config.Messages.REMINDER_MONTHLY_SOH_SUMMARY) %
                                            {"submitted": 0,
                                             "total": 3,
                                             "not_responding": 3} }
        self.runScript(script)

        script = """
            778 > Hmk Id 400 Dp 569 Ip 678
            779 > Hmk Id 400 Dp 569 Ip 678
        """
        self.runScript(script)
        
        script = """
            777 > test soh_report TEST DISTRICT
            777 < %(test_handler_confirm)s
            777 < %(report_results)s
        """ % {"test_handler_confirm": _(config.Messages.TEST_HANDLER_CONFIRM),
               "report_results":       _(config.Messages.REMINDER_MONTHLY_SOH_SUMMARY) %
                                            {"submitted": 2,
                                             "total": 3,
                                             "not_responding": 1} }
        self.runScript(script)

