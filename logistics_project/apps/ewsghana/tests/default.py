from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
from logistics.models import Location, SupplyPoint, SupplyPointType
from logistics_project.apps.ewsghana import app as logistics_app

class TestDefaults (TestScript):
    apps = ([logistics_app.App])
    fixtures = ["ghana_initial_data.json"] 
    def setUp(self):
        TestScript.setUp(self)
        location = Location.objects.get(code='de')
        facilitytype = SupplyPointType.objects.get(code='hc')
        rms = SupplyPoint.objects.get(code='garms')
        facility = SupplyPoint(code='dedh', name='Dangme East District Hospital',
                       location=location, active=True,
                       type=facilitytype, supplied_by=rms)
        facility.save()

    def testDefault(self):
        a = """
           16176023315 > register stella dedh
           16176023315 < Congratulations stella, you have successfully been registered for the Early Warning System. Your facility is Dangme East District Hospital
           16176023315 > xx10
           16176023315 < xx is not a recognized commodity code. Please contact your DHIO or RHIO for help.
           """
        self.runScript(a)


