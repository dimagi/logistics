from rapidsms.tests.scripted import TestScript
from logistics.apps.malawi.const import Messages


class testContactsAndRoles(TestScript):
    
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
            """ % {"required": Messages.REGISTRATION_REQUIRED_MESSAGE}
        self.runScript(a)
        
        
    def testRolesAndOperations(self):
        a = """
                5551111 > register hsa 1 1001
                5551111 < Congratulations hsa, you have successfully been registered for the Early Warning System. Your facility is Bua
                5551112 > manage in charge ic 1001
                5551112 < Congratulations in charge, you have successfully been registered for the Early Warning System. Your facility is Bua
                5551111 > ready 100100
                5551111 < %(bad_perms)s
                5551111 > os 100100
                5551111 < %(bad_perms)s
                5551111 > report 100101 soh la 200
                5551111 < %(bad_perms)s
                5551111 > report 100101 rec la 200
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
            """ % {"bad_perms": Messages.UNSUPPORTED_OPERATION}
        self.runScript(a)