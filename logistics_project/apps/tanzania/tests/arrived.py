from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from django.utils.translation import ugettext as _
from django.utils import translation
from logistics.util import config

class TestArrival(TanzaniaTestScriptBase):

    def testArrivedHelp(self):
        translation.activate("en")
        script = """
          743 > arrived
          743 < %(arrived_help)s
        """ % {"arrived_help": _(config.Messages.ARRIVED_HELP)}
        self.runScript(script)

    def testArrivedUnknownCode(self):
        translation.activate("en")
        script = """
          743 > arrived NOTACODEINTHESYSTEM
          743 < %(arrived_default)s
        """ % {"arrived_default": _(config.Messages.ARRIVED_DEFAULT)}
        self.runScript(script)

    def testArrivedKnownCode(self):
        translation.activate("en")
        script = """
          743 > arrived D10001
          743 < %(arrived_known)s
        """ % {"arrived_known": _(config.Messages.ARRIVED_KNOWN) % {"facility": "VETA 1"}}
        self.runScript(script)

    def testArrivedWithTime(self):
        translation.activate("en")
        script = """
          743 > arrived D10001 10:00
          743 < %(arrived_known)s
        """ % {"arrived_known": _(config.Messages.ARRIVED_KNOWN) % {"facility": "VETA 1"}}
        self.runScript(script)