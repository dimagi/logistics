from __future__ import absolute_import
from rapidsms.tests.scripted import TestScript

from logistics.apps.malawi import app as malawi_app
from logistics.apps.malawi.tests.util import create_hsa, create_manager

class TestAddRemoveProducts(TestScript):
    apps = ([malawi_app.App])
    fixtures = ["malawi_products.json"]

    def testAddProduct(self):
        create_hsa(self, "16175551234", "stella")
        a = """
           16175551234 > add zi
           16175551234 < foo
           """
        self.runScript(a)
