from logistics.apps.logistics.util import config
from logistics.apps.malawi.tests.util import create_hsa, create_manager
from logistics.apps.malawi.tests.base import MalawiTestBase


class testContactsAndRoles(MalawiTestBase):
    
    def testContactRequired(self):
        a = """
                5551212 > soh la 200
                5551212 < %(required)s
                5551212 > eo la 200
                5551212 < %(required)s
                5551212 > rec la 200
                5551212 < %(required)s
                5551212 > report 100101 soh la 200
                5551212 < %(required)s
                5551212 > report 100101 rec la 200
                5551212 < %(required)s
                5551212 > ready 100100
                5551212 < %(required)s
                5551212 > os 100100
                5551212 < %(required)s
                5551212 > confirm
                5551212 < %(required)s
                5551212 > give 100101 la 200
                5551212 < %(required)s
            """ % {"required": config.Messages.REGISTRATION_REQUIRED_MESSAGE}
        self.runScript(a)
        
        
    def testRolesAndOperations(self):
        create_hsa(self, "5551111", "hsa")
        create_manager(self, "5551112", "charles") # in charge!
        create_manager(self, "5551113", "pill pusher", "dp")
        
        a = """
                5551111 > ready 100100
                5551111 < %(bad_perms)s
                5551111 > os 100100
                5551111 < %(bad_perms)s
                5551112 > soh la 200
                5551112 < %(bad_perms)s
                5551112 > eo la 200
                5551112 < %(bad_perms)s
                # doesn't work yet.
                # 5551112 > rec la 200
                # 5551112 < %(bad_perms)s
                5551112 > give 100101 la 200
                5551112 < %(bad_perms)s
                5551112 > confirm
                5551112 < %(bad_perms)s
                5551113 > report 100101 soh la 200
                5551113 < %(bad_perms)s
                5551113 > report 100101 rec la 200
                5551113 < %(bad_perms)s
            """ % {"bad_perms": config.Messages.UNSUPPORTED_OPERATION}
        self.runScript(a)