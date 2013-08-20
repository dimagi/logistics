from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user
from logistics.util import config
from django.utils import translation
from django.utils.translation import ugettext_noop as _

class TestLanguage(TanzaniaTestScriptBase):

    def _verify_language(self, language, phone_number):
        previous_language = translation.get_language()
        translation.activate(language)
        expected = _(config.Messages.HELP_REGISTERED)
        translation.activate(previous_language)
        script = """
          %(phone)s > help
          %(phone)s < %(help_registered)s
        """ % {'phone': phone_number, 'help_registered': expected}
        self.runScript(script)

    def testLanguageEnglish(self):
        translation.activate("en")
        contact = register_user(self, "778", "someone", "d10001")
        script = """
            778 > language en
            778 < %(language_confirm)s
            """ % {'language_confirm': _(config.Messages.LANGUAGE_CONFIRM) % {"language": "English"}}
        self.runScript(script)
        self._verify_language('en', '778')

    def testLanguageSwahili(self):
        translation.activate("sw")
        contact = register_user(self, "779", "someone", "d10001")
        script = """
            779 > lugha sw
            779 < %(language_confirm)s
            """ % {'language_confirm': _(config.Messages.LANGUAGE_CONFIRM) % {"language": "Swahili"}}
        self.runScript(script)
        self._verify_language('sw', '779')


    def testLanguageUnknown(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone", "d10001")
        script = """
            778 > language de
            778 < %(language_unknown)s
            """ % {'language_unknown': _(config.Messages.LANGUAGE_UNKNOWN) % {"language": "de"}}
        self.runScript(script)