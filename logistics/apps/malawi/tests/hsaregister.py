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
    fixtures = ["ghana_initial_data.json"]
    
    def setUp(self):
        TestScript.setUp(self)
        location = Location.objects.get(code='de')
        facilitytype = SupplyPointType.objects.get(code='hc')
        rms = Facility.objects.get(code='garms')
        Facility.objects.get_or_create(code='dedh', name='Dangme East District Hospital',
                                       location=location, active=True,
                                       type=facilitytype, supplied_by=rms)

    def testRegister(self):
        a = """
              8005551212 > hsareg
              8005551212 < %(help_message)s
              8005551212 > hsareg stella
              8005551212 < %(help_message)s
              8005551212 > hsareg stella 115 doesntexist
              8005551212 < Sorry, can't find the location with FACILITY CODE doesntexist
              8005551212 > hsareg stella 115 dedh
              8005551212 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
            """ % {'register_message':REGISTER_MESSAGE, 'help_message':HELP_MESSAGE}
        self.runScript(a)
        loc = Location.objects.get(code="dedh115")
        sp = SupplyPoint.objects.get(code="dedh115")
        self.assertEqual(sp.location, loc)
