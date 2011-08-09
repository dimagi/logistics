from logistics.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics.apps.tanzania.tests.util import register_user
from django.utils.translation import ugettext as _
from logistics.apps.logistics.util import config
from django.utils import translation

class TestLanguage(TanzaniaTestScriptBase):

    def testLanguageEnglish(self):
        translation.activate("en")
        contact = register_user(self, "778", "someone", "d10001")
        script = """
            778 > language en
            778 < %(language_confirm)s
            """ % {'language_confirm': _(config.Messages.LANGUAGE_CONFIRM) % {"language": "English"}}
        self.runScript(script)

    def testLanguageSwahili(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone", "d10001")
        script = """
            778 > lugha sw
            778 < %(language_confirm)s
            """ % {'language_confirm': _(config.Messages.LANGUAGE_CONFIRM) % {"language": "Swahili"}}
        self.runScript(script)

    def testLanguageUnknown(self):
        translation.activate("en")
        contact = register_user(self, "778", "someone", "d10001")
        script = """
            778 > language de
            778 < %(language_unknown)s
            """ % {'language_unknown': _(config.Messages.LANGUAGE_UNKNOWN) % {"language": "de"}}
        self.runScript(script)