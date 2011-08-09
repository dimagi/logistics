from logistics_project.apps.tanzania import loader
from logistics_project.apps.malawi.tests.base import OutputtingTestScript
from logistics.models import SupplyPoint, SupplyPointType
from logistics.util import config
from logistics.loader.base import load_roles, load_report_types
import os


class TanzaniaTestScriptBase(OutputtingTestScript):
    """
    Base test class that prepopulates tests with tanzania's static data
    """
    fixtures = ["tz_static.json", ]
    # this is so the paths line up
    output_directory = os.path.join(os.path.dirname(__file__), "testscripts")
    
    def setUp(self):
        super(TanzaniaTestScriptBase, self).setUp()
        loader.init_static_data()
        
                            
    def tearDown(self):
        super(TanzaniaTestScriptBase, self).tearDown()
        