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
                5551212 > add zi
                5551212 < %(required)s
                5551212 > remove zi
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
        create_manager(self, "5551113", "pill pusher", "dp", facility_code="26")
        
        a = """
                5551111 > ready 100100
                5551111 < %(bad_perms)s
                5551111 > os 100100
                5551111 < %(bad_perms)s
                5551112 > soh la 200
                5551112 < %(bad_perms)s
                5551112 > eo la 200
                5551112 < %(bad_perms)s
                5551112 > add zi
                5551112 < %(bad_perms)s
                5551112 > remove zi
                5551112 < %(bad_perms)s
                5551112 > rec la 200
                5551112 < %(bad_perms)s
                5551112 > give 100101 la 200
                5551112 < %(bad_perms)s
                5551112 > confirm
                5551112 < %(bad_perms)s
            """ % {"bad_perms": config.Messages.UNSUPPORTED_OPERATION}
        self.runScript(a)

    def testRolePermissions(self):

        a = """
                5552222 > manage foo bar dp 2616
                5552222 < %(bad_level)s
                5552222 > manage foo bar dp 26
                5552222 < %(confirm)s
                5552223 > manage second guy dp 26
                5552223 < %(duplicate)s
            """ % {"bad_level": config.Messages.ROLE_WRONG_LEVEL % {'role': 'district pharmacist',
                                                                    'level': 'facility'},
                   "confirm": config.Messages.REGISTRATION_CONFIRM % {'contact_name': 'foo bar',
                                                                      'role': 'district pharmacist',
                                                                      'sp_name':'Machinga'},
                   "duplicate": config.Messages.ROLE_ALREADY_FILLED % {'role': 'district pharmacist'}}
        self.runScript(a)

        a = """
                5553333 > manage baz quux ic 26
                5553333 < %(bad_level)s
                5553333 > manage baz quux ic 2616
                5553333 < %(confirm)s
                5552223 > manage second guy ic 2616
                5552223 < %(duplicate)s
            """ % {"bad_level": config.Messages.ROLE_WRONG_LEVEL % {'role': 'in charge',
                                                                    'level': 'district'},
                   "confirm": config.Messages.REGISTRATION_CONFIRM % {'contact_name': 'baz quux',
                                                                      'role': 'in charge',
                                                                      'sp_name':'Ntaja'},
                   "duplicate": config.Messages.ROLE_ALREADY_FILLED % {'role': 'in charge'}}
        self.runScript(a)
