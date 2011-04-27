from rapidsms.tests.scripted import TestScript
from logistics.apps.malawi.const import Messages


class testContactsAndRoles(TestScript):
    
    def testContactRequired(self):
        a = """
                5551212 > soh la 200
                5551212 < %(required)s
                5551212 > eo la 200
                5551212 < %(required)s
                5551212 > report 100101 soh la 200
                5551212 < %(required)s
                5551212 > report 100101 rec la 200
                5551212 < %(required)s
                5551212 > ready 100100
                5551212 < %(required)s
                5551212 > os 100100
                5551212 < %(required)s
            """ % {"required": Messages.REGISTRATION_REQUIRED_MESSAGE}
        self.runScript(a)
        
        