from logistics import settings
from logistics.apps.malawi import loader
from logistics.apps.malawi.tests.base import OutputtingTestScript
from logistics.apps.logistics.models import SupplyPoint, SupplyPointType
from logistics.apps.logistics.util import config
from logistics.loader.base import load_roles, load_report_types
import os


class TanzaniaTestScriptBase(OutputtingTestScript):
    """
    Base test class that prepopulates tests with tanzania's static data
    """
    
    # this is so the paths line up
    output_directory = os.path.join(os.path.dirname(__file__), "testscripts")
    
    def setUp(self):
        super(TanzaniaTestScriptBase, self).setUp()
        load_roles()
        load_report_types()
        
        # create a few supply points types
        self.fac_type = SupplyPointType.objects.create(name="Facility",
                                                       code=config.SupplyPointCodes.FACILITY)
        self.dist_type = SupplyPointType.objects.create(name="District", 
                                                       code=config.SupplyPointCodes.DISTRICT)
        self.facility = SupplyPoint.objects.create\
                            (code="d10001",name="Test Facility", type=self.fac_type)
        self.district = SupplyPoint.objects.create\
                            (code="d10002",name="Test District", type=self.dist_type)
                            
    def tearDown(self):
        super(TanzaniaTestScriptBase, self).tearDown()
        self.fac_type.delete()
        self.dist_type.delete()
        self.facility.delete()
        self.district.delete()