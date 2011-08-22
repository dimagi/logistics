from logistics_project.apps.tanzania import loader
from logistics_project.apps.malawi.tests.base import OutputtingTestScript
import os
from django.conf import settings

class TanzaniaTestScriptBase(OutputtingTestScript):
    """
    Base test class that prepopulates tests with tanzania's static data
    """
    # this is so the paths line up
    output_directory = os.path.join(os.path.dirname(__file__), "testscripts")
    # hack the static locations to only load a very minor subset
    settings.STATIC_LOCATIONS = "%s%s" % (settings.STATIC_LOCATIONS[:-4], "_test.csv")
    
    def setUp(self):
        super(TanzaniaTestScriptBase, self).setUp()
        loader.init_static_data()
                            
    def tearDown(self):
        super(TanzaniaTestScriptBase, self).tearDown()
        