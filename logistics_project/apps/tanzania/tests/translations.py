from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user
from django.utils.translation import ugettext as _
from logistics.util import config
from django.utils import translation
import inspect

class TestTranslations(TanzaniaTestScriptBase):

    def testLanguageEnglish(self):
        translation.activate("sw")
        count = 0
        for key, value in inspect.getmembers(config.Messages, (lambda x: isinstance(x, str))):
            if (value == _(value)) and \
               (value != "logistics_project.apps.tanzania.config"):
                print "No Swahili translation for \"%s\"" % value
                count+=1
        print "Number of strings w/o translation: %d" % count
        self.assertEqual(count, 0)
