from rapidsms.tests.scripted import TestScript
from logistics_project.apps.ilsgateway.models import ServiceDeliveryPoint, ServiceDeliveryPointStatus, ServiceDeliveryPointStatusType
import ilsgateway.app as ilsgateway_app
from datetime import datetime, timedelta

class TestReminders (TestScript):
    apps = ([ilsgateway_app.App])

    def setUp(self):
        TestScript.setUp(self)
        ServiceDeliveryPoint.objects.all().delete()

    def test_all(self):
        sdp = ServiceDeliveryPoint(name="Test SDP")
        self.assertEqual(sdp.name, "Test SDP")
        sdp.save() 
        
        self.assertFalse(sdp.received_reminder_after("r_and_r_reminder_sent_facility", datetime(datetime.now().year, datetime.now().month, 1) - timedelta(seconds=1)))
        
        #create a reminder
        st = ServiceDeliveryPointStatusType.objects.filter(short_name="r_and_r_reminder_sent_facility")[0:1].get()
        ns = ServiceDeliveryPointStatus(service_delivery_point=sdp, status_type=st, status_date=datetime.now())
        ns.save()
           
        #check reminder
        self.assertTrue(sdp.received_reminder_after("r_and_r_reminder_sent_facility", datetime(datetime.now().year, datetime.now().month, 1) - timedelta(seconds=1)))
        
    def tearDown(self):
        pass
