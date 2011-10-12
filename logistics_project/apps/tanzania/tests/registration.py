from logistics_project.apps.tanzania.tests.base import TanzaniaTestScriptBase
from django.utils.translation import ugettext as _
from django.utils import translation
from logistics.util import config
from logistics.models import SupplyPoint

class TestRegistration(TanzaniaTestScriptBase):

    def testRegisterFacility(self):
        translation.activate("sw")
        sp = SupplyPoint.objects.get(code="D10001")
        script = """
          743 > sajili Alfred Mchau d10001
          743 < %(registration_confirm)s
        """ % {"registration_confirm": _(config.Messages.REGISTRATION_CONFIRM) % {"sdp_name": sp.name,
                                                      "msd_code": "d10001" ,
                                                      "contact_name":"Alfred Mchau"}}
        self.runScript(script)

    def testRegisterFacilityUnknownCode(self):
        translation.activate("sw")
        script = """
          743 > sajili Alfred Mchau d12345
          743 < %(registration_unknown_code)s
        """ % {"registration_unknown_code": _(config.Messages.REGISTER_UNKNOWN_CODE) % {"msd_code": "d12345"}}
        self.runScript(script)

    def testRegisterDistrictLowercase(self):
        translation.activate("sw")
        sp = SupplyPoint.objects.get(name="TANDAHIMBA")
        script = """
          743 > sajili Alfred Mchau : tandahimba
          743 < %(registration_confirm)s
        """ % {"registration_confirm": _(config.Messages.REGISTRATION_CONFIRM_DISTRICT) % {"sdp_name": sp.name,
                                                      "contact_name":"Alfred Mchau"}}
        self.runScript(script)

    def testRegisterDistrictUppercase(self):
        translation.activate("sw")
        sp = SupplyPoint.objects.get(name="TANDAHIMBA")
        script = """
          743 > sajili Alfred Mchau : TANDAHIMBA
          743 < %(registration_confirm)s
        """ % {"registration_confirm": _(config.Messages.REGISTRATION_CONFIRM_DISTRICT) % {"sdp_name": sp.name,
                                                      "contact_name":"Alfred Mchau"}}
        self.runScript(script)

    def testRegisterDistrictMixedCase(self):
        translation.activate("sw")
        sp = SupplyPoint.objects.get(name="TANDAHIMBA")
        script = """
          743 > sajili Alfred Mchau : TANDAhimbA
          743 < %(registration_confirm)s
        """ % {"registration_confirm": _(config.Messages.REGISTRATION_CONFIRM_DISTRICT) % {"sdp_name": sp.name,
                                                      "contact_name":"Alfred Mchau"}}
        self.runScript(script)

    def testRegisterDistrictMultipleWord(self):
        translation.activate("sw")
        sp = SupplyPoint.objects.get(name="TANDAHIMBA")
        sp.name = "TANDAHIMBA RURAL"
        sp.save()

        script = """
          743 > sajili Alfred Mchau : TANDAHIMBA RURAL
          743 < %(registration_confirm)s
        """ % {"registration_confirm": _(config.Messages.REGISTRATION_CONFIRM_DISTRICT) % {"sdp_name": sp.name,
                                                      "contact_name":"Alfred Mchau"}}
        self.runScript(script)

    def testRegisterDistrictMultipleWordDoesNotExist(self):
        translation.activate("sw")
        script = """
          743 > sajili Alfred Mchau : tandahimba rural place
          743 < %(registration_unknown_district)s
        """ % {"registration_unknown_district": _(config.Messages.REGISTER_UNKNOWN_DISTRICT) % {"name": "tandahimba rural place"}}
        self.runScript(script)

    def testRegisterDistrictForgotSeparator(self):
        translation.activate("sw")
        script = """
          743 > sajili Alfred Mchau tandahimba
          743 < %(registration_help)s
        """ % {"registration_help": _(config.Messages.REGISTER_HELP)}
        self.runScript(script)

    def testRegisterFacilityForgotMsdCode(self):
        translation.activate("sw")
        script = """
          743 > sajili Alfred Mchau
          743 < %(registration_help)s
        """ % {"registration_help": _(config.Messages.REGISTER_HELP)}
        self.runScript(script)

    def testRegisterDistrictMixedSpacingForSeparator(self):
        translation.activate("sw")
        sp = SupplyPoint.objects.get(name="TANDAHIMBA")
        script = """
          743 > sajili Alfred Mchau: tandahimba
          743 < %(registration_confirm)s
        """ % {"registration_confirm": _(config.Messages.REGISTRATION_CONFIRM_DISTRICT) % {"sdp_name": sp.name,
                                                      "contact_name":"Alfred Mchau"}}
        self.runScript(script)

        script = """
          743 > sajili Alfred Mchau :tandahimba
          743 < %(registration_confirm)s
        """ % {"registration_confirm": _(config.Messages.REGISTRATION_CONFIRM_DISTRICT) % {"sdp_name": sp.name,
                                                      "contact_name":"Alfred Mchau"}}
        self.runScript(script)

        script = """
          743 > sajili Alfred Mchau  :  tandahimba
          743 < %(registration_confirm)s
        """ % {"registration_confirm": _(config.Messages.REGISTRATION_CONFIRM_DISTRICT) % {"sdp_name": sp.name,
                                                      "contact_name":"Alfred Mchau"}}
        self.runScript(script)
