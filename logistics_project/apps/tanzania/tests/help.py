from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user
from logistics.apps.logistics.util import config
from django.utils.translation import ugettext as _

class TestHelp(TanzaniaTestScriptBase):
    
    def testHelp(self):

#        Swahili
        script = """
          743 > help
          743 < %(help_unregistered)s
        """ % {'help_unregistered': _(config.Messages.HELP_UNREGISTERED)}
        self.runScript(script)
        
        contact = register_user(self, "778", "someone")
        script = """
          778 > help
          778 < %(help_registered)s
        """ % {'help_registered': _(config.Messages.HELP_REGISTERED)}
        self.runScript(script)
        