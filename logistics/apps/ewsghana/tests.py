from rapidsms.tests.scripted import TestScript
from logistics.apps.logistics.models import Location, Facility, SupplyPointType 
from logistics.apps.ewsghana.handlers.registration import HELP_MESSAGE

class TestRegister(TestScript):
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
              8005551212 > register
              8005551212 < %(register_message)s
              8005551212 > register stella
              8005551212 < Sorry, I didn't understand. To register, send register <name> <facility code>. Example: register john dwdh'
              8005551212 > register stella doesntexist
              8005551212 < Sorry, can't find the location with CODE doesntexist
              8005551212 > register stella dedh
              8005551212 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
            """ % {'register_message':HELP_MESSAGE}
        self.runScript(a)

    def testRegisterTwice(self):
        a = """
              8005551212 > register stella dedh
              8005551212 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
              8005551212 > register cynthia dedh
              8005551212 < Congratulations cynthia, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
            """
        self.runScript(a)
