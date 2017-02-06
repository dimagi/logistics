from logistics_project.apps.malawi.tests.base import MalawiTestBase
from logistics_project.apps.malawi.tests.util import create_manager
from static.malawi import config


class MalawiFacilityLevelTestBase(MalawiTestBase):

    def _setup_users(self):
        ic = create_manager(self, "16175551000", "wendy", config.Roles.IN_CHARGE, "2616")
        sh = create_manager(self, "16175551001", "sally", config.Roles.HSA_SUPERVISOR, "2616")
        he = create_manager(self, "16175551002", "robert", config.Roles.EPI_FOCAL, "2616")
        dp = create_manager(self, "16175551003", "ruth", config.Roles.DISTRICT_PHARMACIST, "26")
        de = create_manager(self, "16175551004", "peter", config.Roles.DISTRICT_EPI_COORDINATOR, "26")
        re = create_manager(self, "16175551005", "sam", config.Roles.REGIONAL_EPI_COORDINATOR, "se")
        return (ic, sh, he, dp, de, re)
