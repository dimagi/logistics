from rapidsms.models import Contact
from logistics.apps.malawi.handlers.deregistration import NOT_REGISTERED_MESSAGE
__author__ = 'ternus'
from rapidsms.tests.scripted import TestScript
from logistics.apps.logistics.models import Location, SupplyPoint, ContactRole
from logistics.apps.malawi.handlers.registration import REGISTER_MESSAGE, HSA_HELP_MESSAGE
from logistics.apps.malawi import app as malawi_app, const

class TestHSARegister(TestScript):
    apps = ([malawi_app.App])
    
    def testRegister(self):
        a = """
              8005551212 > reg
              8005551212 < %(help_message)s
              8005551212 > reg stella
              8005551212 < %(help_message)s
              8005551212 > reg stella 1 doesntexist
              8005551212 < Sorry, can't find the location with CODE doesntexist
              8005551212 > reg stella 1 2616
              8005551212 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Ntaja
            """ % {'register_message':REGISTER_MESSAGE, 'help_message':HSA_HELP_MESSAGE}
        self.runScript(a)
        loc = Location.objects.get(code="26161")
        sp = SupplyPoint.objects.get(code="26161")
        self.assertEqual(sp.location, loc)

    def testRegisterMultiName(self):
        a = """
              8005551212 > reg john wilkes booth 1 2616
              8005551212 < Congratulations john wilkes booth, you have successfully been registered for the Early Warning System. Your facility is Ntaja
            """
        self.runScript(a)
        
    def testDuplicateId(self):
        a = """
              8005551212 > reg stella 1 2616
              8005551212 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Ntaja
              8005551213 > reg dupe 1 2616
              8005551213 < Sorry, a location with 26161 already exists. Another HSA may have already registered this ID
            """ 
        self.runScript(a)
    
    def testRoles(self):
        a = """
              8005551212 > reg hsa 1 2616
              8005551212 < Congratulations hsa, you have successfully been registered for the Early Warning System. Your facility is Ntaja
            """
        self.runScript(a)
        # default to HSA
        self.assertEqual(ContactRole.objects.get(code=const.ROLE_HSA),Contact.objects.get(name="hsa").role)
        
        b = """
              8005551214 > manage incharge ic 2616
              8005551214 < Congratulations incharge, you have successfully been registered for the Early Warning System. Your facility is Ntaja
            """ 
        self.runScript(b)
        self.assertEqual(ContactRole.objects.get(code=const.ROLE_IN_CHARGE),Contact.objects.get(name="incharge").role)
    
    def testManager(self):
        a = """
              8005551214 > manage incharge ic 2616
              8005551214 < Congratulations incharge, you have successfully been registered for the Early Warning System. Your facility is Ntaja
            """ 
        self.runScript(a)
        
    def testLeave(self):
        a = """
              8005551212 > reg stella 1 2616
              8005551212 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Ntaja
              8005551212 > reg stella 1 2616
              8005551212 < You are already registered. To change your information you must first text LEAVE
              8005551213 > leave
              8005551213 < %(not_registered)s
            """ % {"not_registered": NOT_REGISTERED_MESSAGE}
        self.runScript(a)
        contact = Contact.objects.get(name="stella")
        self.assertTrue(contact.is_active)
        b = """
              8005551212 > leave
              8005551212 < You have successfully left the Stock Alert system. Goodbye!
            """ 
        self.runScript(b)
        contact = Contact.objects.get(name="stella")
        self.assertFalse(contact.is_active)
        c = """
              8005551212 > reg stella 1 2616
              8005551212 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Ntaja
            """ 
        self.runScript(c)
        contact = Contact.objects.get(name="stella")
        self.assertTrue(contact.is_active)
        