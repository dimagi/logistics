from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user
from logistics.util import config
from django.utils.translation import ugettext as _
from django.utils import translation

class TestHelp(TanzaniaTestScriptBase):

    def testHelpUnregistered(self):
        translation.activate("en")
        
        # Unregistered user
        script = """
          743 > help
          743 < %(help_unregistered)s
        """ % {'help_unregistered': _(config.Messages.HELP_UNREGISTERED)}
        self.runScript(script)

    def testHelpRegistered(self):
        translation.activate("sw")
        
        # Registered user
        contact = register_user(self, "778", "someone")
        script = """
          778 > msaada
          778 < %(help_registered)s
        """ % {'help_registered': _(config.Messages.HELP_REGISTERED)}
        self.runScript(script)

        # Registered user
        contact = register_user(self, "779", "someone")
        script = """
          779 > help
          779 < %(help_registered)s
        """ % {'help_registered': _(config.Messages.HELP_REGISTERED)}
        self.runScript(script)
