from rapidsms.models import Contact
from logistics.apps.malawi.const import Messages
__author__ = 'ternus'
from rapidsms.tests.scripted import TestScript
from logistics.apps.logistics.models import Location, SupplyPoint, ContactRole,\
    REGISTER_MESSAGE
from logistics.apps.malawi import app as malawi_app
from logistics.apps.malawi import const

class TestHSARegister(TestScript):
    apps = ([malawi_app.App])
    
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
            """ % {'register_message':REGISTER_MESSAGE, 'help_message':Messages.HSA_HELP,
                   'bad_loc': Messages.UNKNOWN_LOCATION % {"code": "doesntexist"},
                   "confirm": Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
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
            """ % {"confirm": Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                               "role": "hsa",
                                                               "contact_name": "john wilkes booth"}}
        self.runScript(a)
        
    def testDuplicateId(self):
        a = """
              8005551212 > reg stella 1 2616
              8005551212 < %(confirm)s
              8005551213 > reg dupe 1 2616
              8005551213 < Sorry, a location with 261601 already exists. Another HSA may have already registered this ID
            """ % {"confirm": Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
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
            """  % {"confirm": Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                                "role": "hsa",
                                                                "contact_name": "hsa"}}
        
        self.runScript(a)
        # default to HSA
        self.assertEqual(ContactRole.objects.get(code=const.Roles.HSA),Contact.objects.get(name="hsa").role)
        
        b = """
              8005551214 > manage incharge ic 2616
              8005551214 < %(confirm)s
            """ % {"confirm": Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                                "role": "in charge",
                                                                "contact_name": "incharge"}}
        self.runScript(b)
        self.assertEqual(ContactRole.objects.get(code=const.Roles.IN_CHARGE),Contact.objects.get(name="incharge").role)
    
    def testManager(self):
        a = """
              8005551214 > manage incharge ic 2616
              8005551214 < %(confirm)s
            """ % {"confirm": Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                               "role": "in charge",
                                                               "contact_name": "incharge"}}
        self.runScript(a)
        
    def testLeave(self):
        a = """
              8005551212 > reg stella 1 2616
              8005551212 < %(confirm)s
              8005551212 > reg stella 1 2616
              8005551212 < You are already registered. To change your information you must first text LEAVE
              8005551213 > leave
              8005551213 < %(not_registered)s
            """ % {"not_registered": Messages.LEAVE_NOT_REGISTERED,
                   "confirm": Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                               "role": "hsa",
                                                               "contact_name": "stella"}}
        self.runScript(a)
        contact = Contact.objects.get(name="stella")
        self.assertTrue(contact.is_active)
        b = """
              8005551212 > leave
              8005551212 < %(left)s
            """ % {"left": Messages.LEAVE_CONFIRM}
        self.runScript(b)
        contact = Contact.objects.get(name="stella")
        self.assertFalse(contact.is_active)
        c = """
              8005551212 > reg stella 1 2616
              8005551212 < %(confirm)s
            """ % {"confirm": Messages.REGISTRATION_CONFIRM % {"sp_name": "Ntaja",
                                                               "role": "hsa",
                                                               "contact_name": "stella"}}
        self.runScript(c)
        contact = Contact.objects.get(name="stella")
        self.assertTrue(contact.is_active)
    