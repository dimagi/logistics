from rapidsms.models import Contact
__author__ = 'ternus'
import unittest
from django import forms
from rapidsms.conf import settings
from rapidsms.tests.scripted import TestScript
from logistics.apps.registration.forms import IntlSMSContactForm
from logistics.apps.logistics.models import Location, Facility, SupplyPointType,\
    SupplyPoint
from logistics.apps.malawi.handlers.registration import REGISTER_MESSAGE, HELP_MESSAGE
from logistics.apps.malawi import app as malawi_app

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
              8005551212 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Ntaja            """ % {'register_message':REGISTER_MESSAGE, 'help_message':HELP_MESSAGE}
        self.runScript(a)
        loc = Location.objects.get(code="26161")
        sp = SupplyPoint.objects.get(code="26161")
        self.assertEqual(sp.location, loc)

    def testDuplicateId(self):
        a = """
              8005551212 > reg stella 1 2616
              8005551212 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Ntaja
              8005551213 > reg dupe 1 2616
              8005551213 < Sorry, a location with 26161 already exists. Another HSA may have already registered this ID
            """ 
        self.runScript(a)
    
    def testLeave(self):
        a = """
              8005551212 > reg stella 1 2616
              8005551212 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Ntaja
              8005551212 > reg stella 1 2616
              8005551212 < Sorry, a location with 26161 already exists. Another HSA may have already registered this ID
            """ 
        self.runScript(a)
        contact = Contact.objects.get(name="stella")
        self.assertTrue(contact.is_active)
        b = """
              8005551212 > leave
              8005551212 < You have successfully left the Stock Alert system. Goodbye!
            """ 
        self.runScript(b)
        contact = Contact.objects.get(name="stella")
        self.assertTrue(contact.is_active)
        c = """
              8005551212 > reg stella 1 2616
              8005551212 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Ntaja
            """ 
        self.runScript(c)
        contact = Contact.objects.get(name="stella")
        self.assertTrue(contact.is_active)
        