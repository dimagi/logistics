from rapidsms.tests.scripted import TestScript
from logistics.apps.ilsgateway.models import ServiceDeliveryPoint
import ilsgateway.app as ilsgateway_app

class TestServiceDeliveryPoint (TestScript):
    apps = ([ilsgateway_app.App])

    def setUp(self):
        TestScript.setUp(self)
        ServiceDeliveryPoint.objects.all().delete()

    def test_all(self):
        sdp = ServiceDeliveryPoint(name="Test SDP")
        self.assertEqual(sdp.name, "Test SDP")
        sdp.save()    
        
    def tearDown(self):
        pass
