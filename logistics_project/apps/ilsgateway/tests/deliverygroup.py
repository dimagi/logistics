from rapidsms.tests.scripted import TestScript
from logistics_project.apps.ilsgateway.models import DeliveryGroup
import ilsgateway.app as ilsgateway_app

class TestDeliveryGroup (TestScript):
    apps = ([ilsgateway_app.App])

    def setUp(self):
        TestScript.setUp(self)
        DeliveryGroup.objects.all().delete()

    def test_all(self):
        dg = DeliveryGroup(name="A")
        self.assertEqual(dg.name, "A")    