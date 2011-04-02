from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
import logistics.apps.logistics.app as logistics_app
from logistics.apps.logistics.models import Location, Facility, SupplyPointType

class TestReceipts (TestScript):
    apps = ([logistics_app.App])

    def setUp(self):
        TestScript.setUp(self)
        location = Location.objects.get(code='de')
        facilitytype = SupplyPointType.objects.get(code='hc')
        rms = Facility.objects.get(code='garms')
        facility = Facility(code='dedh', name='Dangme East District Hospital',
                       location=location, active=True,
                       type=facilitytype, supplied_by=rms)
        facility.save()

    def testReceipt(self):
        a = """
           16176023315 > register stella dedh
           16176023315 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > xx10
           16176023315 < xx is not a recognized commodity code. Please contact FRHP for assistance.
           16176023315 > dasdfa
           16176023315 < Sorry, I could not understand your message. Please contact Focus Region Health Project for help.
           16176023315 > adsf
           16176023315 < Stock report should contain quantity of stock on hand. Please contact FRHP for assistance.
           """
        self.runScript(a)

