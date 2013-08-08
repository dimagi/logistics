from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from logistics_project.apps.tanzania.tests.util import register_user,\
    add_products
from logistics.util import config
from django.utils.translation import ugettext as _
from django.utils import translation

class TestBugs(TanzaniaTestScriptBase):

    def testUnicodeCharacters(self):
        translation.activate("sw")
        contact = register_user(self, "778", "someone")
        add_products(contact, ["id", "dp", "ip"])
        script = u"""
            778 > Hmk Id 400 \u0660Dp 569 Ip 678 
            778 < %(soh_confirm)s
        """ % {"soh_confirm": _(config.Messages.SOH_CONFIRM)}
        self.runScript(script)
