from rapidsms.models import Contact
from logistics_project.apps.malawi.tests.base import MalawiTestBase
from logistics_project.apps.malawi.tests.util import create_manager, create_hsa,\
    report_stock
from logistics.models import Location, SupplyPoint, ContactRole
from logistics.util import config

class TestHSARegister(MalawiTestBase):
    
    def testRegister(self):
        a = """
              8005551212 > reg
              8005551212 < %(help_message)s
              8005551212 > reg stella
              8005551212 < %(help_message)s
              8005551212 > reg stella 1 doesntexist
              8005551212 < %(bad_loc)s
              8005551212 > reg stella 1 2616
              8005551212 < %(confirm)s
            """ % {'register_message':config.Messages.REGISTER_MESSAGE, 'help_message':config.Messages.HSA_HELP,
                   'bad_loc': config.Messages.UNKNOWN_LOCATION % {"code": "doesntexist"},
                   "confirm": config.Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                               "role": "hsa",
                                                               "contact_name": "stella"}}
        self.runScript(a)
        loc = Location.objects.get(code="261601")
        sp = SupplyPoint.objects.get(code="261601")
        self.assertEqual(sp.location, loc)

    def testRegisterMultiName(self):
        a = """
              8005551212 > reg john wilkes booth 1 2616
              8005551212 < %(confirm)s
            """ % {"confirm": config.Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                               "role": "hsa",
                                                               "contact_name": "john wilkes booth"}}
        self.runScript(a)
        
    def testDuplicateId(self):
        a = """
              8005551212 > reg stella 1 2616
              8005551212 < %(confirm)s
              8005551213 > reg dupe 1 2616
              8005551213 < Sorry, a location with 261601 already exists. Another HSA may have already registered this ID
            """ % {"confirm": config.Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                               "role": "hsa",
                                                               "contact_name": "stella"}}
        self.runScript(a)
    
    def testBadIds(self):
        a = """
              8005551212 > reg stella 0 2616
              8005551212 < id must be a number between 1 and 99. 0 is out of range
              8005551212 > reg stella -5 2616
              8005551212 < id must be a number between 1 and 99. -5 is out of range
              8005551212 > reg stella 100 2616
              8005551212 < id must be a number between 1 and 99. 100 is out of range
              8005551212 > reg stella o1 2616
              8005551212 < id must be a number between 1 and 99. o1 is not a number
              8005551212 > reg stella i 2616
              8005551212 < id must be a number between 1 and 99. i is not a number
              8005551212 > reg stella pi 2616
              8005551212 < id must be a number between 1 and 99. pi is not a number
              8005551212 > reg stella 1.0 2616
              8005551212 < id must be a number between 1 and 99. 1.0 is not a number
            """ 
        self.runScript(a)
    
    def testRoles(self):
        a = """
              8005551212 > reg hsa 1 2616
              8005551212 < %(confirm)s
            """  % {"confirm": config.Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                                "role": "hsa",
                                                                "contact_name": "hsa"}}
        
        self.runScript(a)
        # default to HSA
        self.assertEqual(ContactRole.objects.get(code=config.Roles.HSA),Contact.objects.get(name="hsa").role)
        
        b = """
              8005551214 > manage incharge ic 2616
              8005551214 < %(confirm)s
            """ % {"confirm": config.Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                                "role": "in charge",
                                                                "contact_name": "incharge"}}
        self.runScript(b)
        self.assertEqual(ContactRole.objects.get(code=config.Roles.IN_CHARGE),Contact.objects.get(name="incharge").role)
    
    def testManager(self):
        a = """
              8005551214 > manage incharge ic 2616
              8005551214 < %(confirm)s
            """ % {"confirm": config.Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                               "role": "in charge",
                                                               "contact_name": "incharge"}}
        self.runScript(a)

        a = """
              8005551215 > manage district dp 26
              8005551215 < %(confirm)s
            """ % {"confirm": config.Messages.REGISTRATION_DISTRICT_CONFIRM % {"sp_name": "Machinga",
                                                               "role": "district pharmacist",
                                                               "contact_name": "district"}}
        self.runScript(a)
        
    def testLeave(self):
        a = """
              8005551212 > reg stella 1 2616
              8005551212 < %(confirm)s
              8005551212 > reg stella 1 2616
              8005551212 < You are already registered. To change your information you must first text LEAVE
              8005551213 > leave
              8005551213 < %(not_registered)s
            """ % {"not_registered": config.Messages.LEAVE_NOT_REGISTERED,
                   "confirm": config.Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                               "role": "hsa",
                                                               "contact_name": "stella"}}
        self.runScript(a)
        contact = Contact.objects.get(name="stella")
        self.assertTrue(contact.is_active)
        spi = contact.supply_point.id

        b = """
              8005551212 > leave
              8005551212 < %(left)s
            """ % {"left": config.Messages.LEAVE_CONFIRM}
        self.runScript(b)
        contact = Contact.objects.get(name="stella")
        self.assertFalse(contact.is_active)
        c = """
              8005551212 > reg stella 1 2616
              8005551212 < %(confirm)s
            """ % {"confirm": config.Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                               "role": "hsa",
                                                               "contact_name": "stella"}}
        self.runScript(c)
        contact = Contact.objects.get(name="stella")
        self.assertTrue(contact.is_active)
        self.assertEqual(contact.supply_point.id, spi)


    def testQuit(self):
        a = """
              8005551212 > reg stella 1 2616
              8005551212 < %(confirm)s
              8005551212 > reg stella 1 2616
              8005551212 < You are already registered. To change your information you must first text LEAVE
              8005551213 > quit
              8005551213 < %(not_registered)s
            """ % {"not_registered": config.Messages.LEAVE_NOT_REGISTERED,
                   "confirm": config.Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                               "role": "hsa",
                                                               "contact_name": "stella"}}
        self.runScript(a)
        contact = Contact.objects.get(name="stella")
        self.assertTrue(contact.is_active)
        spi = contact.supply_point.id
        spn = contact.supply_point.code
        b = """
              8005551212 > quit
              8005551212 < %(left)s
            """ % {"left": config.Messages.LEAVE_CONFIRM}
        self.runScript(b)
        contact = Contact.objects.get(name="stella")
        self.assertFalse(contact.is_active)
        self.assertFalse(SupplyPoint.objects.get(id=spi).active)
        self.assertNotEqual(SupplyPoint.objects.get(id=spi).code, spn)
        
        c = """
              8005551212 > reg stella 1 2616
              8005551212 < %(confirm)s
            """ % {"confirm": config.Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                               "role": "hsa",
                                                               "contact_name": "stella"}}
        self.runScript(c)
        contact = Contact.objects.get(name="stella")
        self.assertTrue(contact.is_active)
        self.assertNotEqual(contact.supply_point.id, spi)

    def testManagerLeave(self):
        hsa = create_hsa(self, "555555", "somehsa", products="la zi")
        ic = create_manager(self, "666666", "somemanager")
        super = create_manager(self, "777777", "somesuper", config.Roles.HSA_SUPERVISOR)
        report_stock(self, hsa, "zi 10 la 15", [ic, super], "zi 190, la 345")
        b = """
              666666 > leave
              666666 < %(left)s
            """ % {"left": config.Messages.LEAVE_CONFIRM}
        self.runScript(b)
        failed = False
        try:
            report_stock(self, hsa, "zi 10 la 15", [ic, super], "zi 190, la 345")
        except Exception:
            # this is expected
            failed = True
        if not failed:
            self.fail("Reporting stock should not have notified the supervisor")
        report_stock(self, hsa, "zi 10 la 15", [super], "zi 190, la 345")

    def _run_manager_mismatch_test(self, role_code, supply_point_code):
        role = ContactRole.objects.get(code=role_code)
        supply_point = SupplyPoint.objects.get(code=supply_point_code)
        a = """
          9990000000001 > manage test %(role_code)s %(supply_point_code)s
          9990000000001 < %(response)s
        """ % {
            'role_code': role_code,
            'supply_point_code': supply_point_code,
            'response': config.Messages.ROLE_WRONG_LEVEL % {'role': role.name, 'level': supply_point.location.type.name},
        }
        self.runScript(a)

    def testMismatchedManagerRolesAndLocations(self):
        self._run_manager_mismatch_test(config.Roles.IN_CHARGE, '26')
        self._run_manager_mismatch_test(config.Roles.IN_CHARGE, 'se')
        self._run_manager_mismatch_test(config.Roles.IN_CHARGE, 'malawi')
        self._run_manager_mismatch_test(config.Roles.DISTRICT_PHARMACIST, '2616')
        self._run_manager_mismatch_test(config.Roles.DISTRICT_PHARMACIST, 'se')
        self._run_manager_mismatch_test(config.Roles.DISTRICT_PHARMACIST, 'malawi')
        self._run_manager_mismatch_test(config.Roles.REGIONAL_EPI_COORDINATOR, '2616')
        self._run_manager_mismatch_test(config.Roles.REGIONAL_EPI_COORDINATOR, '26')
        self._run_manager_mismatch_test(config.Roles.REGIONAL_EPI_COORDINATOR, 'malawi')
