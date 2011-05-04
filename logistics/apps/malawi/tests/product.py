from __future__ import absolute_import
from rapidsms.tests.scripted import TestScript

from logistics.apps.malawi import load_static_data
from logistics.apps.malawi import app as malawi_app
from logistics.apps.malawi.tests.util import create_hsa, create_manager

class TestAddRemoveProducts(TestScript):
    apps = ([malawi_app.App])
    fixtures = ["malawi_products.json"]

    def setUp(self):
        TestScript.setUp(self)
        load_static_data()
    
    def testAddRemoveProduct(self):
        create_hsa(self, "16175551234", "stella")
        a = """
           16175551234 > add quux
           16175551234 < Sorry, no product matches code quux.  Nothing done.
           16175551234 > add zi
           16175551234 < Thank you, you are now supplying: zi
           16175551234 > add zi de
           16175551234 < You are already supplying: zi. Nothing done.
           16175551234 > add de
           16175551234 < Thank you, you are now supplying: de
           16175551234 > remove cm
           16175551234 < You are not currently supplying: cm. Nothing done.
           16175551234 > remove de
           16175551234 < Thank you, you no longer supply: de
           """
        self.runScript(a)
